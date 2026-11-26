import { useEffect, useRef, useState } from 'react';
import { listQuizzes, startQuiz, submitAnswer } from '../api/quizzes';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';

export default function QuizzesPage() {
  const quizzes = useResource(listQuizzes);
  const [quiz, setQuiz] = useState(null);
  const [attempt, setAttempt] = useState(null);
  const [answer, setAnswer] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(null);
  const [retryAnswer, setRetryAnswer] = useState(false);
  const busy = useRef(false);
  const answerInput = useRef(null);
  const questionId = attempt?.question?.id;

  useEffect(() => {
    // Move focus to the answer field after the server advances the question.
    if (questionId) answerInput.current?.focus();
  }, [questionId]);

  async function start(selectedQuiz) {
    if (busy.current) return;
    busy.current = true;
    setPending(true);
    setError(null);
    try {
      const state = await startQuiz(selectedQuiz.id);
      setQuiz(selectedQuiz);
      setAttempt(state);
      setAnswer('');
      setRetryAnswer(false);
    } catch (failure) {
      setError(failure);
    } finally {
      busy.current = false;
      setPending(false);
    }
  }

  async function submit(event) {
    event.preventDefault();
    if (busy.current || !questionId || !answer.trim()) return;
    busy.current = true;
    setPending(true);
    setError(null);
    try {
      // The server owns progress and accepts an exact retry without grading twice.
      setAttempt(await submitAnswer(attempt.quiz_attempt_id, questionId, answer));
      setAnswer('');
      setRetryAnswer(false);
    } catch (failure) {
      setError(failure);
      // A lost response may still have saved the answer. Keep its text for retry.
      setRetryAnswer(!failure.status || failure.status < 400 || failure.status >= 500);
    } finally {
      busy.current = false;
      setPending(false);
    }
  }

  function backToQuizzes() {
    setAttempt(null);
    setAnswer('');
    setRetryAnswer(false);
    setError(null);
    quizzes.reload();
  }

  return (
    <div className="study-workspace flashcards-workspace">
      <PageHeader title="Quizzes" />
      {!attempt && (
        <section className="panel study-setup" aria-busy={quizzes.loading || pending}>
          <h2>Choose a quiz</h2>
          {quizzes.loading && <p className="page-status" role="status">Loading quizzes.</p>}
          {quizzes.error && <RequestError error={quizzes.error} onRetry={quizzes.reload} />}
          {quizzes.data?.length === 0 && <p>No quizzes are available yet.</p>}
          {quizzes.data?.map((item) => {
            const attemptsUsed = item.attempt_count >= item.attempt_limit;
            const canOpen = item.can_resume || !attemptsUsed;
            return (
            <div className="study-bottom" key={item.id}>
              <div>
                <h3>{item.title}</h3>
                {item.description && <p>{item.description}</p>}
                <dl className="quiz-stats">
                  <div><dt>Latest score</dt><dd>{formatScore(item.last_score)}</dd></div>
                  <div><dt>Average score</dt><dd>{formatScore(item.average_score)}</dd></div>
                  <div><dt>Attempts used</dt><dd>{item.attempt_count} / {item.attempt_limit}</dd></div>
                </dl>
              </div>
              {canOpen ? (
                <button className="button button-primary" disabled={pending} onClick={() => start(item)}>
                  {pending ? 'Opening quiz…' : item.can_resume ? 'Resume quiz' : 'Start quiz'}
                </button>
              ) : <span>No attempts left</span>}
            </div>
            );
          })}
        </section>
      )}
      {attempt?.status === 'in_progress' && (
        <section className="panel study-card-panel" aria-busy={pending}>
          <div className="section-heading">
            <span className="card-source">{quiz.title}</span>
            <span className="card-source" role="status">
              Question {attempt.question_index + 1} of {attempt.total_questions}
            </span>
          </div>
          <progress className="study-progress" max={attempt.total_questions}
            value={attempt.question_index} aria-label="Quiz progress" />
          <h2 className="study-question" id="quiz-question">{attempt.question.question}</h2>
          <form onSubmit={submit}>
            <div className="form-field">
              <label htmlFor="quiz-answer">Your answer</label>
              <input id="quiz-answer" ref={answerInput} aria-describedby="quiz-question"
                value={answer} onChange={(event) => setAnswer(event.target.value)}
                readOnly={pending || retryAnswer} required />
            </div>
            <div className="record-actions quiz-answer-actions">
              <button className="button button-primary" disabled={pending || !answer.trim()}>
                {pending ? 'Submitting…' : retryAnswer ? 'Retry answer' : 'Submit answer'}
              </button>
              <button className="button button-secondary" type="button"
                disabled={pending} onClick={backToQuizzes}>Back to quizzes</button>
            </div>
          </form>
        </section>
      )}
      {attempt?.status === 'completed' && (
        <section className="panel study-summary" aria-live="polite">
          <h2>{quiz.title} complete</h2>
          <p>Final score: <strong>{attempt.score}%</strong></p>
          <button className="button button-primary" onClick={backToQuizzes}>Back to quizzes</button>
        </section>
      )}
      {error && <RequestError error={error} />}
    </div>
  );
}

function formatScore(score) {
  return score == null ? '—' : `${score}%`;
}
