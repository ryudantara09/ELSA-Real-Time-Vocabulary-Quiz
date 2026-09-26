export type ConnectionStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "disconnected"
  | "error";

export interface Question {
  question_id: string;
  prompt: string;
  choices: string[];
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  score: number;
}

export interface ConnectedMessage {
  type: "connected";
  quiz_id: string;
  user_id: string;
  display_name: string;
  questions: Question[];
  leaderboard: LeaderboardEntry[];
}

export interface AnswerResultMessage {
  type: "answer_result";
  question_id: string;
  correct: boolean;
  score: number;
}

export interface LeaderboardMessage {
  type: "leaderboard";
  leaderboard: LeaderboardEntry[];
}

export interface ErrorMessage {
  type: "error";
  code: string;
  message: string;
  question_id?: string;
  correct?: boolean;
  score?: number;
}

export type ServerMessage =
  | ConnectedMessage
  | AnswerResultMessage
  | LeaderboardMessage
  | ErrorMessage;

export interface ParticipantResponse {
  user_id: string;
  display_name: string;
  score: number;
}

function isQuestion(value: unknown): value is Question {
  if (!value || typeof value !== "object") {
    return false;
  }
  const question = value as Record<string, unknown>;
  return (
    typeof question.question_id === "string" &&
    typeof question.prompt === "string" &&
    Array.isArray(question.choices) &&
    question.choices.every((choice) => typeof choice === "string")
  );
}

function isLeaderboard(value: unknown): value is LeaderboardEntry[] {
  if (!Array.isArray(value)) {
    return false;
  }
  return value.every((item) => {
    if (!item || typeof item !== "object") {
      return false;
    }
    const entry = item as Record<string, unknown>;
    return (
      typeof entry.rank === "number" &&
      typeof entry.user_id === "string" &&
      typeof entry.display_name === "string" &&
      typeof entry.score === "number"
    );
  });
}

export function parseServerMessage(value: unknown): ServerMessage | null {
  if (!value || typeof value !== "object") {
    return null;
  }
  const message = value as Record<string, unknown>;
  if (message.type === "connected") {
    if (
      typeof message.quiz_id !== "string" ||
      typeof message.user_id !== "string" ||
      typeof message.display_name !== "string" ||
      !Array.isArray(message.questions) ||
      !message.questions.every(isQuestion) ||
      !isLeaderboard(message.leaderboard)
    ) {
      return null;
    }
    return {
      type: "connected",
      quiz_id: message.quiz_id,
      user_id: message.user_id,
      display_name: message.display_name,
      questions: message.questions,
      leaderboard: message.leaderboard,
    };
  }
  if (message.type === "answer_result") {
    if (
      typeof message.question_id !== "string" ||
      typeof message.correct !== "boolean" ||
      typeof message.score !== "number"
    ) {
      return null;
    }
    return {
      type: "answer_result",
      question_id: message.question_id,
      correct: message.correct,
      score: message.score,
    };
  }
  if (message.type === "leaderboard") {
    if (!isLeaderboard(message.leaderboard)) {
      return null;
    }
    return { type: "leaderboard", leaderboard: message.leaderboard };
  }
  if (message.type === "error") {
    if (typeof message.code !== "string" || typeof message.message !== "string") {
      return null;
    }
    return {
      type: "error",
      code: message.code,
      message: message.message,
      question_id: typeof message.question_id === "string" ? message.question_id : undefined,
      correct: typeof message.correct === "boolean" ? message.correct : undefined,
      score: typeof message.score === "number" ? message.score : undefined,
    };
  }
  return null;
}
