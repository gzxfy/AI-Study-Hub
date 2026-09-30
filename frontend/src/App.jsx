import { Navigate, Route, Routes } from 'react-router';
import AppLayout from './layouts/AppLayout';
import DashboardPage from './pages/DashboardPage';
import FeaturePage from './pages/FeaturePage';
import NotFoundPage from './pages/NotFoundPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="/app" element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="notes" element={<FeaturePage title="Notes" description="A place for the ideas you want to understand." stage="5" detail="Your notes, search, PDF import, and editing will be connected here." />} />
        <Route path="topics" element={<FeaturePage title="Topics" description="Give your study materials a little structure." stage="6" detail="Your topics and their associated notes will appear here." />} />
        <Route path="flashcards" element={<FeaturePage title="Flashcards" description="Turn what you know into something you can recall." stage="7" detail="Create and organize flashcards from your notes once the flashcard API is ready." />} />
        <Route path="study" element={<FeaturePage title="Study" description="Make room for a focused review." stage="7" detail="Choose a note, reveal each answer, and record whether you got it right using the existing study API." />} />
        <Route path="assistant" element={<FeaturePage title="AI Assistant" description="Work through your study material, one question at a time." stage="8" detail="Select a note and continue its saved conversation. Note and topic context will be clearly identified." />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
