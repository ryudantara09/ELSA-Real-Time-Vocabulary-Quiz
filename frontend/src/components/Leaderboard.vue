<script setup lang="ts">
import type { LeaderboardEntry } from "../types/quiz";

defineProps<{
  entries: LeaderboardEntry[];
  currentUserId: string;
  highlightedUserIds: string[];
}>();
</script>

<template>
  <section class="board">
    <h2>Leaderboard</h2>
    <ol>
      <li
        v-for="entry in entries"
        :key="entry.user_id"
        :class="{
          me: entry.user_id === currentUserId,
          flash: highlightedUserIds.includes(entry.user_id),
        }"
      >
        <span>{{ entry.rank }}. {{ entry.display_name }}</span>
        <strong>{{ entry.score }}</strong>
      </li>
    </ol>
    <p v-if="entries.length === 0">No participants yet.</p>
  </section>
</template>

<style scoped>
.board {
  display: grid;
  gap: 0.5rem;
  align-content: start;
}

h2 {
  margin: 0;
  font-size: 1.1rem;
}

ol {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.35rem;
}

li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.45rem 0.6rem;
  border: 1px solid #d7d7d7;
}

.me {
  border-color: #1d4e89;
}

.flash {
  background: #e5f6ea;
}

p {
  margin: 0;
}
</style>
