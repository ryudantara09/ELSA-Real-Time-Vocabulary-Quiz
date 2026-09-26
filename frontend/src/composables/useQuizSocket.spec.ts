import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useQuizSocket } from "./useQuizSocket";

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

function host() {
  return defineComponent({
    setup() {
      return useQuizSocket();
    },
    template: "<div />",
  });
}

function emit(message: unknown): void {
  const socket = FakeWebSocket.latest;
  if (!socket?.onmessage) {
    throw new Error("socket is not open");
  }
  socket.onmessage({ data: JSON.stringify(message) } as MessageEvent<string>);
}

describe("quiz socket", () => {
  beforeEach(() => {
    sessionStorage.clear();
    FakeWebSocket.latest = null;
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes("/missing/")) {
          return new Response("{}", { status: 404 });
        }
        return new Response(
          JSON.stringify({ user_id: "user-1", display_name: "Ada", score: 0 }),
          { status: 200 },
        );
      }),
    );
  });

  it("shows an error when the quiz does not exist", async () => {
    const wrapper = mount(host());

    await wrapper.vm.join("missing", "Ada");

    expect(wrapper.vm.errorMessage).toBe("Quiz was not found");
    expect(wrapper.vm.status).toBe("error");
    expect(FakeWebSocket.latest).toBeNull();
  });

  it("shows the question and score from the server", async () => {
    const wrapper = mount(host());

    await wrapper.vm.join("quiz-1", "Ada");
    emit(connected);
    await flushPromises();

    expect(wrapper.vm.status).toBe("connected");
    expect(wrapper.vm.currentQuestion.prompt).toContain("short time");
    expect(wrapper.vm.score).toBe(0);
    expect(wrapper.vm.leaderboard).toEqual(connected.leaderboard);
  });

  it("updates the score after an answer and a later leaderboard", async () => {
    const wrapper = mount(host());
    await wrapper.vm.join("quiz-1", "Ada");
    emit(connected);

    wrapper.vm.submitAnswer("q1", "ephemeral");
    emit({
      type: "answer_result",
      question_id: "q1",
      correct: true,
      score: 1,
    });
    emit({
      type: "leaderboard",
      leaderboard: [
        { rank: 1, user_id: "user-1", display_name: "Ada", score: 1 },
        { rank: 2, user_id: "user-2", display_name: "Grace", score: 0 },
      ],
    });
    await flushPromises();

    expect(JSON.parse(FakeWebSocket.latest?.sent[0] ?? "")).toEqual({
      type: "submit_answer",
      question_id: "q1",
      choice: "ephemeral",
    });
    expect(wrapper.vm.feedback).toBe("Correct");
    expect(wrapper.vm.score).toBe(1);
    expect(wrapper.vm.leaderboard[1].display_name).toBe("Grace");
  });

  it("shows disconnected when the socket closes", async () => {
    const wrapper = mount(host());
    await wrapper.vm.join("quiz-1", "Ada");
    emit(connected);

    FakeWebSocket.latest?.onclose?.({} as CloseEvent);
    await flushPromises();

    expect(wrapper.vm.status).toBe("disconnected");
  });

  it("keeps the current leaderboard when a message is unexpected", async () => {
    const wrapper = mount(host());
    await wrapper.vm.join("quiz-1", "Ada");
    emit(connected);

    emit({ type: "leaderboard", leaderboard: "nope" });
    await flushPromises();

    expect(wrapper.vm.feedback).toBe("Received an unexpected update");
    expect(wrapper.vm.leaderboard).toEqual(connected.leaderboard);
  });
});
