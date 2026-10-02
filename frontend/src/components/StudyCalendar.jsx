import { useState } from 'react';
import Icon from './Icon';

const weekdays = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

export default function StudyCalendar() {
  const today = new Date();
  const [month, setMonth] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));
  const firstWeekday = (month.getDay() + 6) % 7;
  const daysInMonth = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
  const label = month.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  function moveMonth(offset) {
    setMonth(new Date(month.getFullYear(), month.getMonth() + offset, 1));
  }

  return (
    <section className="calendar" aria-labelledby="calendar-title">
      <div className="section-heading"><h2 id="calendar-title">Calendar</h2><button className="text-button" onClick={() => setMonth(new Date(today.getFullYear(), today.getMonth(), 1))}>Today</button></div>
      <div className="calendar-heading"><span aria-live="polite">{label}</span><div className="calendar-controls"><button className="icon-button" aria-label="Previous month" onClick={() => moveMonth(-1)}><span className="rotate"><Icon name="chevron" size={14} /></span></button><button className="icon-button" aria-label="Next month" onClick={() => moveMonth(1)}><Icon name="chevron" size={14} /></button></div></div>
      <div className="calendar-grid" aria-label={label}>
        {weekdays.map((day) => <span className="weekday" key={day}>{day}</span>)}
        {Array.from({ length: firstWeekday }, (_, i) => <span key={`blank-${i}`} />)}
        {Array.from({ length: daysInMonth }, (_, i) => {
          const day = i + 1;
          const isToday = day === today.getDate() && month.getMonth() === today.getMonth() && month.getFullYear() === today.getFullYear();
          return <span key={day} className={`calendar-day ${isToday ? 'is-today' : ''}`} aria-current={isToday ? 'date' : undefined}>{day}</span>;
        })}
      </div>
      <p className="calendar-caption"><span className="status-dot" /> Today</p>
    </section>
  );
}
