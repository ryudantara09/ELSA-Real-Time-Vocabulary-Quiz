<script setup lang="ts">
import type { ConnectionStatus } from "../types/quiz";

defineProps<{
  status: ConnectionStatus;
  quizId: string;
  message: string;
}>();

const emit = defineEmits<{
  reconnect: [];
}>();

const labels: Record<ConnectionStatus, string> = {
  idle: "Idle",
  connecting: "Connecting",
  connected: "Connected",
  disconnected: "Disconnected",
  error: "Error",
};
</script>

<template>
  <div class="status">
    <p>
      <span :class="status">{{ labels[status] }}</span>
      <span v-if="quizId">Quiz {{ quizId }}</span>
    </p>
    <p v-if="message" class="message">{{ message }}</p>
    <button
      v-if="status === 'disconnected' || status === 'error'"
      type="button"
      @click="emit('reconnect')"
    >
      Reconnect
    </button>
  </div>
</template>

<style scoped>
.status {
  display: grid;
  gap: 0.35rem;
}

p {
  margin: 0;
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

span:first-child {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.connected {
  color: #0f7b3a;
}

.connecting {
  color: #8a5a00;
}

.disconnected,
.error {
  color: #9b1c1c;
}

.message {
  color: #9b1c1c;
}

button {
  font: inherit;
  width: fit-content;
  padding: 0.35rem 0.7rem;
}
</style>
