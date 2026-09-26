import { computed, onUnmounted, ref } from "vue";
import {
  parseServerMessage,
  type ConnectionStatus,
  type ErrorMessage,
  type LeaderboardEntry,
  type ParticipantResponse,
  type Question,
} from "../types/quiz";

const HIGHLIGHT_MS = 1200;
const SESSION_KEY = "vocabulary-quiz-session";
const EXPIRED_QUIZ_MESSAGE = "This quiz is no longer available. Join again.";
const UNEXPECTED_MESSAGE = "Received an unexpected update";

interface SavedSession {
  quizId: string;
  userId: string;
  displayName: string;
  questionIndex: number;
}

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
      writeSession();
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

  function leave(): void {
    closeSocket();
    clearSavedSession();
    resetQuizState();
    status.value = "idle";
    errorMessage.value = "";
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
      writeSession();
    }
  }

  function showNext(): void {
    if (questionIndex.value < questions.value.length - 1) {
      questionIndex.value += 1;
      clearFeedback();
      writeSession();
    }
  }

  function openSocket(): void {
    closeSocket();
    submitting.value = false;
    status.value = "connecting";
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${protocol}://${window.location.host}/ws/quizzes/${encodeURIComponent(quizId.value)}/participants/${encodeURIComponent(userId.value)}`;
    const next = new WebSocket(url);
    socket = next;

    next.onmessage = (event: MessageEvent<string>) => {
      if (socket !== next) {
        return;
      }
      let payload: unknown;
      try {
        payload = JSON.parse(event.data) as unknown;
      } catch {
        noteUnexpectedMessage();
        return;
      }
      handleMessage(payload);
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

  function handleMessage(payload: unknown): void {
    const message = parseServerMessage(payload);
    if (!message) {
      noteUnexpectedMessage();
      return;
    }
    if (message.type === "connected") {
      status.value = "connected";
      errorMessage.value = "";
      const hadQuestions = questions.value.length > 0;
      const sameQuestions =
        hadQuestions &&
        message.questions.length === questions.value.length &&
        message.questions.every(
          (question, index) => question.question_id === questions.value[index]?.question_id,
        );
      questions.value = message.questions;
      if (questionIndex.value >= message.questions.length || (hadQuestions && !sameQuestions)) {
        questionIndex.value = 0;
      }
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
    if (message.code === "quiz_not_found" || message.code === "participant_not_found") {
      expireSession();
      return;
    }
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

  function expireSession(): void {
    closeSocket();
    clearSavedSession();
    resetQuizState();
    status.value = "error";
    errorMessage.value = EXPIRED_QUIZ_MESSAGE;
  }

  function noteUnexpectedMessage(): void {
    if (status.value === "connected") {
      feedbackCorrect.value = null;
      feedback.value = UNEXPECTED_MESSAGE;
      return;
    }
    errorMessage.value = UNEXPECTED_MESSAGE;
  }

  function resetQuizState(): void {
    quizId.value = "";
    userId.value = "";
    displayName.value = "";
    questions.value = [];
    questionIndex.value = 0;
    leaderboard.value = [];
    score.value = 0;
    answered.value = {};
    submitting.value = false;
    joining.value = false;
    highlightedUserIds.value = [];
    clearFeedback();
  }

  function writeSession(): void {
    const saved: SavedSession = {
      quizId: quizId.value,
      userId: userId.value,
      displayName: displayName.value,
      questionIndex: questionIndex.value,
    };
    try {
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(saved));
    } catch {
      // The tab still works when storage is blocked.
    }
  }

  function clearSavedSession(): void {
    try {
      sessionStorage.removeItem(SESSION_KEY);
    } catch {
      return;
    }
  }

  function readSession(): SavedSession | null {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY);
      if (!raw) {
        return null;
      }
      const parsed: unknown = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object") {
        return null;
      }
      const session = parsed as Record<string, unknown>;
      if (
        typeof session.quizId !== "string" ||
        typeof session.userId !== "string" ||
        typeof session.displayName !== "string" ||
        !session.quizId ||
        !session.userId
      ) {
        return null;
      }
      const questionIndex =
        typeof session.questionIndex === "number" && session.questionIndex >= 0
          ? session.questionIndex
          : 0;
      return {
        quizId: session.quizId,
        userId: session.userId,
        displayName: session.displayName,
        questionIndex,
      };
    } catch {
      return null;
    }
  }

  function restoreSession(): void {
    const saved = readSession();
    if (!saved) {
      return;
    }
    quizId.value = saved.quizId;
    userId.value = saved.userId;
    displayName.value = saved.displayName;
    questionIndex.value = saved.questionIndex;
    openSocket();
  }

  function closeSocket(): void {
    submitting.value = false;
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

  restoreSession();

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
    leave,
    submitAnswer,
    showPrevious,
    showNext,
  };
}
