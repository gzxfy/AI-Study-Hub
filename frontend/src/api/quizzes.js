import { ApiError, mutate, request } from './client.js';

export async function listQuizzes(signal) {
  const { quizzes } = await request('/api/quizzes', { signal });
  if (!Array.isArray(quizzes) || quizzes.some((quiz) =>
    !Number.isInteger(quiz?.id) || typeof quiz.title !== 'string'
  )) {
    throw new ApiError('The quiz list could not be read.');
  }
  return quizzes;
}

function readAttempt(data) {
  const { question, score, status, total_questions, question_index } = data;
  const validProgress = Number.isInteger(total_questions) && total_questions > 0 &&
    Number.isInteger(question_index) && question_index >= 0;
  const inProgress = status === 'in_progress' && question_index < total_questions &&
    Number.isInteger(question?.id) && typeof question.question === 'string';
  const completed = status === 'completed' && question_index === total_questions &&
    question === null && Number.isFinite(score);

  if (!Number.isInteger(data.quiz_attempt_id) || !validProgress || (!inProgress && !completed)) {
    throw new ApiError('The quiz response could not be verified.');
  }
  return data;
}

export async function startQuiz(quizId) {
  const attempt = readAttempt(await mutate(`/api/quizzes/${quizId}/attempts`));
  if (attempt.quiz_id !== quizId) throw new ApiError('The quiz response could not be verified.');
  return attempt;
}

export async function submitAnswer(attemptId, questionId, answer) {
  const data = await mutate(`/api/quiz-attempts/${attemptId}/answers`, {
    question_id: questionId,
    answer,
  });
  if (data.quiz_attempt_id !== attemptId) throw new ApiError('The quiz response could not be verified.');
  return readAttempt(data);
}
