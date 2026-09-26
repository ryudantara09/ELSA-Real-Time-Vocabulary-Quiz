import { computed, onUnmounted, ref } from "vue";
import type {
  ConnectionStatus,
  ErrorMessage,
  LeaderboardEntry,
  ParticipantResponse,
  Question,
  ServerMessage,
} from "../types/quiz";

const HIGHLIGHT_MS = 1200;

export function useQuizSocket() {
  const status = ref<ConnectionStatus>("idle");
  const errorMessage = ref("");
  const quizId = ref("");
  const userId = ref("");
  const displayName = ref("");
  const questions = ref<Question[]>([]);
  const questionIndex = ref(0);
  const leaderboard = ref<LeaderboardEntry[]>([]);
  const score = ref(0);
  const feedback = ref("");
  const feedbackCorrect = ref<boolean | null>(null);
  const answered = ref<Record<string, boolean>>({});
  const highlightedUserIds = ref<string[]>([]);
  const submitting = ref(false);
  const joining = ref(false);

  let socket: WebSocket | null = null;
  let highlightTimer = 0;

  const currentQuestion = computed(
    () => questions.value[questionIndex.value] ?? null,
  );
  const currentAnswered = computed(() => {
    const question = currentQuestion.value;
    return question ? Boolean(answered.value[question.question_id]) : false;
  });

  async function join(nextQuizId: string, name: string): Promise<void> {
    const cleanedQuizId = nextQuizId.trim();
    const cleanedName = name.trim();
    if (!cleanedQuizId || !cleanedName) {
      status.value = "error";
      errorMessage.value = "Quiz ID and name are required";
      return;
    }

    if (joining.value) {
      return;
    }
    joining.value = true;
    status.value = "connecting";
    errorMessage.value = "";
    try {
      const response = await fetch(
        `/quizzes/${encodeURIComponent(cleanedQuizId)}/participants`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ display_name: cleanedName }),
        },
      );
      if (response.status === 404) {
        status.value = "error";
        errorMessage.value = "Quiz was not found";
        return;
      }
      if (!response.ok) {
        status.value = "error";
        errorMessage.value = "Could not join the quiz";
        return;
      }
      const participant = (await response.json()) as ParticipantResponse;
      quizId.value = cleanedQuizId;
      userId.value = participant.user_id;
      displayName.value = participant.display_name;
      score.value = participant.score;
      openSocket();
    } catch {
      status.value = "error";
      errorMessage.value = "Could not reach the quiz server";
    } finally {
      if (!userId.value) {
        joining.value = false;
      }
    }
  }

  function reconnect(): void {
    if (!quizId.value || !userId.value) {
      return;
    }
    errorMessage.value = "";
    openSocket();
  }

  function submitAnswer(questionId: string, choice: string): void {
    if (
      status.value !== "connected" ||
      submitting.value ||
      answered.value[questionId] ||
      !socket ||
      socket.readyState !== WebSocket.OPEN
    ) {
      return;
    }
    submitting.value = true;
    socket.send(
      JSON.stringify({
        type: "submit_answer",
        question_id: questionId,
        choice,
      }),
    );
  }

  function showPrevious(): void {
    if (questionIndex.value > 0) {
      questionIndex.value -= 1;
      clearFeedback();
    }
  }

  function showNext(): void {
    if (questionIndex.value < questions.value.length - 1) {
      questionIndex.value += 1;
      clearFeedback();
    }
  }

  function openSocket(): void {
    closeSocket();
    status.value = "connecting";
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${protocol}://${window.location.host}/ws/quizzes/${encodeURIComponent(quizId.value)}/participants/${encodeURIComponent(userId.value)}`;
    const next = new WebSocket(url);
    socket = next;

    next.onmessage = (event: MessageEvent<string>) => {
      if (socket !== next) {
        return;
      }
      let message: ServerMessage;
      try {
        message = JSON.parse(event.data) as ServerMessage;
      } catch {
        errorMessage.value = "Received an unreadable message";
        return;
      }
      handleMessage(message);
    };

    next.onerror = () => {
      if (socket !== next || errorMessage.value) {
        return;
      }
      errorMessage.value = "Connection failed";
    };

    next.onclose = () => {
      if (socket !== next) {
        return;
      }
      socket = null;
      submitting.value = false;
      if (status.value === "connected") {
        status.value = "disconnected";
        return;
      }
      if (status.value === "connecting") {
        status.value = "error";
        if (!errorMessage.value) {
          errorMessage.value = "Connection closed";
        }
      }
    };
  }

  function handleMessage(message: ServerMessage): void {
    if (message.type === "connected") {
      status.value = "connected";
      errorMessage.value = "";
      questions.value = message.questions;
      questionIndex.value = 0;
      displayName.value = message.display_name;
      applyLeaderboard(message.leaderboard);
      return;
    }
    if (message.type === "answer_result") {
      submitting.value = false;
      score.value = message.score;
      markAnswered(message.question_id);
      feedbackCorrect.value = message.correct;
      feedback.value = message.correct ? "Correct" : "Not quite";
      return;
    }
    if (message.type === "leaderboard") {
      applyLeaderboard(message.leaderboard);
      return;
    }
    if (message.type === "error") {
      applyError(message);
    }
  }

  function applyError(message: ErrorMessage): void {
    submitting.value = false;
    if (message.code === "already_answered" && message.question_id) {
      markAnswered(message.question_id);
      if (typeof message.score === "number") {
        score.value = message.score;
      }
      feedbackCorrect.value = message.correct ?? null;
      feedback.value = "Already answered";
      return;
    }
    if (status.value === "connected") {
      feedbackCorrect.value = false;
      feedback.value = message.message;
      return;
    }
    errorMessage.value = message.message;
    status.value = "error";
  }

  function applyLeaderboard(next: LeaderboardEntry[]): void {
    const previousScores = new Map(
      leaderboard.value.map((entry) => [entry.user_id, entry.score]),
    );
    const changed = next
      .filter((entry) => {
        const previous = previousScores.get(entry.user_id);
        return previous !== undefined && entry.score > previous;
      })
      .map((entry) => entry.user_id);

    leaderboard.value = next;
    const mine = next.find((entry) => entry.user_id === userId.value);
    if (mine) {
      score.value = mine.score;
    }
    if (changed.length === 0) {
      return;
    }
    highlightedUserIds.value = changed;
    window.clearTimeout(highlightTimer);
    highlightTimer = window.setTimeout(() => {
      highlightedUserIds.value = [];
    }, HIGHLIGHT_MS);
  }

  function markAnswered(questionId: string): void {
    answered.value = { ...answered.value, [questionId]: true };
  }

  function clearFeedback(): void {
    feedback.value = "";
    feedbackCorrect.value = null;
  }

  function closeSocket(): void {
    if (!socket) {
      return;
    }
    const current = socket;
    socket = null;
    current.onmessage = null;
    current.onerror = null;
    current.onclose = null;
    if (
      current.readyState === WebSocket.OPEN ||
      current.readyState === WebSocket.CONNECTING
    ) {
      current.close();
    }
  }

  onUnmounted(() => {
    closeSocket();
    window.clearTimeout(highlightTimer);
  });

  return {
    status,
    errorMessage,
    quizId,
    userId,
    displayName,
    questions,
    questionIndex,
    currentQuestion,
    currentAnswered,
    leaderboard,
    score,
    feedback,
    feedbackCorrect,
    highlightedUserIds,
    submitting,
    joining,
    join,
    reconnect,
    submitAnswer,
    showPrevious,
    showNext,
  };
}
