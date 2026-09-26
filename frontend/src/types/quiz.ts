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
