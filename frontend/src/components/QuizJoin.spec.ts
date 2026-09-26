import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import QuizJoin from "./QuizJoin.vue";

function mountJoin() {
  return mount(QuizJoin, {
    props: { serverError: "", busy: false },
  });
}

describe("Quiz join form", () => {
  it("requires a quiz id and a name", async () => {
    const wrapper = mountJoin();

    await wrapper.get("form").trigger("submit");

    expect(wrapper.text()).toContain("Quiz ID and name are required");
    expect(wrapper.emitted("join")).toBeUndefined();
  });

  it("emits a trimmed quiz id and name", async () => {
    const wrapper = mountJoin();
    await wrapper.get("input[name='quizId']").setValue("  quiz-1  ");
    await wrapper.get("input[name='displayName']").setValue("  Ada  ");

    await wrapper.get("form").trigger("submit");

    expect(wrapper.emitted("join")?.[0]).toEqual(["quiz-1", "Ada"]);
  });
});
