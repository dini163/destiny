import { Link } from 'react-router-dom';
import { ROUTES } from '../../nav';
import { Icon, type IconName } from '../ui/Icon';
const QUESTIONS: {
  title: string;
  label: string;
  body: string;
  to: string;
  icon: IconName;
}[] = [
  {
    title: '我怎样，才能更好地用自己？',
    label: '关于自己',
    body: '看见驱动力、压力反应与相处需求，找到适合自己的节奏。',
    to: ROUTES.baziNatal,
    icon: 'compass',
  },
  {
    title: '我们为什么亲近，又为何摩擦？',
    label: '关于关系',
    body: '从双方的需求与差异出发，把抽象的互补读成可讨论的议题。',
    to: ROUTES.baziHehun,
    icon: 'seal',
  },
  {
    title: '下一阶段，我想怎样安排？',
    label: '关于节奏',
    body: '了解年度与流月的传统解读，再结合自己的现实计划做取舍。',
    to: ROUTES.baziTransit,
    icon: 'clock',
  },
];
export function QuestionEntries() {
  return (
    <section id="questions" className="question-section">
      <div className="discovery-heading">
        <div>
          <h2>此刻，你更想了解什么？</h2>
        </div>
        <p>不必先懂术语，从一个真实的关心开始。</p>
      </div>
      <div className="question-grid">
        {QUESTIONS.map((item, index) => (
          <Link className="question-card" key={item.to} to={item.to}>
            <div className="question-card-top">
              <span>0{index + 1}</span>
              <Icon name={item.icon} size={39} />
            </div>
            <span className="question-kicker">{item.label}</span>
            <h3>{item.title}</h3>
            <p>{item.body}</p>
            <div className="question-card-bottom">
              <span>开始探索</span>
              <span aria-hidden="true">↗</span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
