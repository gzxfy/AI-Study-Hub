import { createBrowserRouter, createRoutesFromElements, Route, RouterProvider } from 'react-router';
import RequireAuth from './auth/RequireAuth';
import AppLayout from './layouts/AppLayout';
import DashboardPage from './pages/DashboardPage';
import AuthPage from './pages/AuthPage';
import FeaturePage from './pages/FeaturePage';
import NotFoundPage from './pages/NotFoundPage';
import NotesPage from './pages/NotesPage';
import CreateNotePage from './pages/CreateNotePage';
import NotePage from './pages/NotePage';
import LogoutPage from './pages/LogoutPage';
import EditNotePage from './pages/EditNotePage';
import TopicsPage from './pages/TopicsPage';
import TopicPage from './pages/TopicPage';
import TopicEditorPage from './pages/TopicEditorPage';

const features = [
  { path: 'flashcards', title: 'Flashcards', description: 'Review key concepts from your notes.' },
  { path: 'study', title: 'Study', description: 'Set aside time to practice what you have learned.' },
  { path: 'assistant', title: 'AI Assistant', description: 'Ask questions about your study materials.' },
];

const router = createBrowserRouter(createRoutesFromElements(
    <>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="app" element={<DashboardPage />} />
        <Route path="logout" element={<LogoutPage />} />
        <Route element={<RequireAuth />}>
          <Route path="app/notes" element={<NotesPage />} />
          <Route path="app/notes/new" element={<CreateNotePage />} />
          <Route path="app/notes/:noteId" element={<NotePage />} />
          <Route path="app/notes/:noteId/edit" element={<EditNotePage />} />
          <Route path="app/topics" element={<TopicsPage />} />
          <Route path="app/topics/new" element={<TopicEditorPage />} />
          <Route path="app/topics/:topicId" element={<TopicPage />} />
          <Route path="app/topics/:topicId/edit" element={<TopicEditorPage />} />
        </Route>
        {features.map(({ path, ...props }) => (
          <Route key={path} path={`app/${path}`} element={<FeaturePage {...props} />} />
        ))}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
      <Route path="login" element={<AuthPage key="login" mode="login" />} />
      <Route path="register" element={<AuthPage key="register" mode="register" />} />
    </>
));

export default function App() {
  return <RouterProvider router={router} />;
}
