import { createBrowserRouter, createRoutesFromElements, Route, RouterProvider } from 'react-router';
import RequireAuth from './auth/RequireAuth';
import AppLayout from './layouts/AppLayout';
import DashboardPage from './pages/DashboardPage';
import AuthPage from './pages/AuthPage';
import FlashcardsPage from './pages/FlashcardsPage';
import FlashcardEditorPage from './pages/FlashcardEditorPage';
import FlashcardStudyPage from './pages/FlashcardStudyPage';
import NotFoundPage from './pages/NotFoundPage';
import NotesPage from './pages/NotesPage';
import CreateNotePage from './pages/CreateNotePage';
import NotePage from './pages/NotePage';
import LogoutPage from './pages/LogoutPage';
import EditNotePage from './pages/EditNotePage';
import TopicsPage from './pages/TopicsPage';
import TopicPage from './pages/TopicPage';
import TopicEditorPage from './pages/TopicEditorPage';
import AssistantPage from './pages/AssistantPage';

const router = createBrowserRouter(createRoutesFromElements(
    <>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="app" element={<DashboardPage />} />
        <Route path="logout" element={<LogoutPage />} />
        <Route element={<RequireAuth />}>
          <Route path="app/flashcards" element={<FlashcardsPage />} />
          <Route path="app/flashcards/new" element={<FlashcardEditorPage />} />
          <Route path="app/flashcards/:cardId/edit" element={<FlashcardEditorPage />} />
          <Route path="app/study" element={<FlashcardStudyPage />} />
          <Route path="app/assistant" element={<AssistantPage />} />
          <Route path="app/notes" element={<NotesPage />} />
          <Route path="app/notes/new" element={<CreateNotePage />} />
          <Route path="app/notes/:noteId" element={<NotePage />} />
          <Route path="app/notes/:noteId/edit" element={<EditNotePage />} />
          <Route path="app/topics" element={<TopicsPage />} />
          <Route path="app/topics/new" element={<TopicEditorPage />} />
          <Route path="app/topics/:topicId" element={<TopicPage />} />
          <Route path="app/topics/:topicId/edit" element={<TopicEditorPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
      <Route path="login" element={<AuthPage key="login" mode="login" />} />
      <Route path="register" element={<AuthPage key="register" mode="register" />} />
    </>
));

export default function App() {
  return <RouterProvider router={router} />;
}
