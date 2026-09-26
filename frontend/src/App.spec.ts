import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App.vue";

class FakeWebSocket {
  static OPEN = 1;
  static CONNECTING = 0;
  static CLOSING = 2;
  static CLOSED = 3;
  static latest: FakeWebSocket | null = null;

  readyState = FakeWebSocket.OPEN;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  sent: string[] = [];

  constructor(public url: string) {
    FakeWebSocket.latest = this;
  }

  send(data: string): void {
    this.sent.push(data);
  }

  close(): void {
    this.readyState = FakeWebSocket.CLOSED;
  }
}

const connected = {
  type: "connected",
  quiz_id: "quiz-1",
  user_id: "user-1",
  display_name: "Ada",
  questions: [
    {
      question_id: "q1",
      prompt: "Which word means lasting for a very short time?",
      choices: ["ephemeral", "permanent", "ancient", "solid"],
    },
  ],
  leaderboard: [{ rank: 1, user_id: "user-1", display_name: "Ada", score: 0 }],
};

function emit(message: unknown): void {
  FakeWebSocket.latest?.onmessage?.({
    data: JSON.stringify(message),
  } as MessageEvent<string>);
}

describe("quiz screen", () => {
  beforeEach(() => {
    sessionStorage.clear();
    FakeWebSocket.latest = null;
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({ user_id: "user-1", display_name: "Ada", score: 0 }),
            { status: 200 },
          ),
      ),
    );
  });

  it("joins, shows the question, and displays the new score", async () => {
    const wrapper = mount(App);
    await wrapper.get("input[name='quizId']").setValue("quiz-1");
    await wrapper.get("input[name='displayName']").setValue("Ada");
    await wrapper.get("form").trigger("submit");
    await flushPromises();
    emit(connected);
    await flushPromises();

    expect(wrapper.text()).toContain("Which word means lasting for a very short time?");
    expect(wrapper.text()).toContain("Your score: 0");

    const choice = wrapper.findAll("button").find((button) => button.text() === "ephemeral");
    await choice?.trigger("click");
    emit({
      type: "answer_result",
      question_id: "q1",
      correct: true,
      score: 1,
    });
    emit({
      type: "leaderboard",
      leaderboard: [{ rank: 1, user_id: "user-1", display_name: "Ada", score: 1 }],
    });
    await flushPromises();

    expect(wrapper.text()).toContain("Correct");
    expect(wrapper.text()).toContain("Your score: 1");
    expect(wrapper.text()).toContain("1. Ada");
  });
});
