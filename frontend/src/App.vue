<script setup lang="ts">
import { computed } from "vue";
import ConnectionStatus from "./components/ConnectionStatus.vue";
import Leaderboard from "./components/Leaderboard.vue";
import QuizJoin from "./components/QuizJoin.vue";
import QuizQuestion from "./components/QuizQuestion.vue";
import { useQuizSocket } from "./composables/useQuizSocket";

const quiz = useQuizSocket();

const showJoin = computed(
  () => quiz.userId.value === "" || quiz.status.value === "idle",
);
const canSubmit = computed(() => quiz.status.value === "connected");
</script>

<template>
  <main class="page">
    <h1>Real-Time Vocabulary Quiz</h1>
    <QuizJoin
      v-if="showJoin"
      :server-error="quiz.status.value === 'error' ? quiz.errorMessage.value : ''"
      :busy="quiz.joining.value"
      @join="quiz.join"
    />
    <section v-else class="live">
      <ConnectionStatus
        :status="quiz.status.value"
        :quiz-id="quiz.quizId.value"
        :message="quiz.errorMessage.value"
        @reconnect="quiz.reconnect"
      />
      <div class="columns">
        <QuizQuestion
          :question="quiz.currentQuestion.value"
          :question-number="quiz.questionIndex.value + 1"
          :question-count="quiz.questions.value.length"
          :score="quiz.score.value"
          :feedback="quiz.feedback.value"
          :feedback-correct="quiz.feedbackCorrect.value"
          :answered="quiz.currentAnswered.value"
          :can-submit="canSubmit"
          :can-go-back="quiz.questionIndex.value > 0"
          :can-go-forward="quiz.questionIndex.value < quiz.questions.value.length - 1"
          @choose="quiz.submitAnswer(quiz.currentQuestion.value?.question_id ?? '', $event)"
          @previous="quiz.showPrevious"
          @next="quiz.showNext"
        />
        <Leaderboard
          :entries="quiz.leaderboard.value"
          :current-user-id="quiz.userId.value"
          :highlighted-user-ids="quiz.highlightedUserIds.value"
        />
      </div>
    </section>
  </main>
</template>

<style scoped>
.page {
  font-family: "Segoe UI", sans-serif;
  color: #1c1c1c;
  max-width: 52rem;
  margin: 0 auto;
  padding: 1.5rem;
}

h1 {
  font-size: 1.6rem;
  margin: 0 0 1rem;
}

.live,
.columns {
  display: grid;
  gap: 1rem;
}

@media (min-width: 720px) {
  .columns {
    grid-template-columns: 1.4fr 0.8fr;
    align-items: start;
  }
}
</style>
