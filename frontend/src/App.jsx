import { Route, Routes } from 'react-router';
import AppLayout from './layouts/AppLayout';
import DashboardPage from './pages/DashboardPage';
import AuthPage from './pages/AuthPage';
import FeaturePage from './pages/FeaturePage';
import NotFoundPage from './pages/NotFoundPage';

const features = [
  { path: 'notes', title: 'Notes', description: 'Your notes and study materials, organized in one place.' },
  { path: 'topics', title: 'Topics', description: 'Group your study materials by subject or course.' },
  { path: 'flashcards', title: 'Flashcards', description: 'Review key concepts from your notes.' },
  { path: 'study', title: 'Study', description: 'Set aside time to practice what you have learned.' },
  { path: 'assistant', title: 'AI Assistant', description: 'Ask questions about your study materials.' },
];

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="app" element={<DashboardPage />} />
        {features.map(({ path, ...props }) => (
          <Route key={path} path={`app/${path}`} element={<FeaturePage {...props} />} />
        ))}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
      <Route path="login" element={<AuthPage key="login" mode="login" />} />
      <Route path="register" element={<AuthPage key="register" mode="register" />} />
    </Routes>
  );
}
