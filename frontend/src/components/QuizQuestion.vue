<script setup lang="ts">
import type { Question } from "../types/quiz";

defineProps<{
  question: Question | null;
  questionNumber: number;
  questionCount: number;
  score: number;
  feedback: string;
  feedbackCorrect: boolean | null;
  answered: boolean;
  canSubmit: boolean;
  canGoBack: boolean;
  canGoForward: boolean;
}>();

const emit = defineEmits<{
  choose: [choice: string];
  previous: [];
  next: [];
}>();
</script>

<template>
  <section class="question">
    <p class="score">Your score: {{ score }}</p>
    <p v-if="!question">Waiting for the quiz.</p>
    <template v-else>
      <p class="count">Question {{ questionNumber }} of {{ questionCount }}</p>
      <h2>{{ question.prompt }}</h2>
      <div class="choices">
        <button
          v-for="choice in question.choices"
          :key="choice"
          type="button"
          :disabled="!canSubmit || answered"
          @click="emit('choose', choice)"
        >
          {{ choice }}
        </button>
      </div>
      <p
        class="feedback"
        :class="{ correct: feedbackCorrect === true, incorrect: feedbackCorrect === false }"
      >
        {{ feedback }}
      </p>
      <div class="nav">
        <button type="button" :disabled="!canGoBack" @click="emit('previous')">
          Previous
        </button>
        <button type="button" :disabled="!canGoForward" @click="emit('next')">
          Next
        </button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.question {
  display: grid;
  gap: 0.75rem;
}

.score,
.count {
  margin: 0;
}

h2 {
  margin: 0;
  font-size: 1.25rem;
}

.choices {
  display: grid;
  gap: 0.5rem;
}

button {
  font: inherit;
  text-align: left;
  padding: 0.5rem 0.7rem;
}

.nav {
  display: flex;
  gap: 0.5rem;
}

.feedback {
  min-height: 1.25rem;
  margin: 0;
  font-weight: 600;
}

.correct {
  color: #0f7b3a;
}

.incorrect {
  color: #9b1c1c;
}
</style>
