<script setup lang="ts">
import { ref } from "vue";

defineProps<{
  serverError: string;
  busy: boolean;
}>();

const emit = defineEmits<{
  join: [quizId: string, displayName: string];
}>();

const quizId = ref("");
const displayName = ref("");
const localError = ref("");
const creating = ref(false);

async function createQuiz(): Promise<void> {
  localError.value = "";
  creating.value = true;
  try {
    const response = await fetch("/quizzes", { method: "POST" });
    if (!response.ok) {
      localError.value = "Could not create a quiz";
      return;
    }
    const body = (await response.json()) as { quiz_id: string };
    quizId.value = body.quiz_id;
  } catch {
    localError.value = "Could not reach the quiz server";
  } finally {
    creating.value = false;
  }
}

function submit(): void {
  localError.value = "";
  if (!quizId.value.trim() || !displayName.value.trim()) {
    localError.value = "Quiz ID and name are required";
    return;
  }
  emit("join", quizId.value.trim(), displayName.value.trim());
}
</script>

<template>
  <form class="join" @submit.prevent="submit">
    <p>Create a quiz, share the ID, then join with a name.</p>
    <button type="button" :disabled="creating" @click="createQuiz">
      Create quiz
    </button>
    <label>
      Quiz ID
      <input v-model="quizId" name="quizId" autocomplete="off" />
    </label>
    <label>
      Name
      <input v-model="displayName" name="displayName" autocomplete="name" />
    </label>
    <p v-if="localError || serverError" class="error">
      {{ localError || serverError }}
    </p>
    <button type="submit" :disabled="busy">Join quiz</button>
  </form>
</template>

<style scoped>
.join {
  display: grid;
  gap: 0.75rem;
  max-width: 28rem;
}

label {
  display: grid;
  gap: 0.25rem;
  font-size: 0.9rem;
}

input {
  font: inherit;
  padding: 0.45rem 0.55rem;
}

button {
  font: inherit;
  padding: 0.45rem 0.75rem;
  width: fit-content;
}

.error {
  color: #9b1c1c;
  margin: 0;
}
</style>
