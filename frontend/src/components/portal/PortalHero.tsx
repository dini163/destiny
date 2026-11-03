import { Link } from 'react-router-dom';
import { useI18n } from '../../i18n/context';
import { ROUTES } from '../../nav';
export function PortalHero() {
  const { t } = useI18n();
  return (
    <section className="discovery-hero">
      <div>
        <h1>
          {t('把古老的智慧，')}
          <br />
          {t('读成自己的答案。')}
        </h1>
        <p className="hero-description">
          {t('从了解自己，到读懂一段关系。')}
          <br />
          {t('把复杂的排盘，整理成你看得懂、用得上的生活观察。')}
        </p>
        <div className="hero-actions">
          <a className="discovery-primary" href="#questions">
            {t('从你关心的问题开始')} <span aria-hidden="true">↗</span>
          </a>
          <Link className="quiet-link" to="/report/r2?sample=1">
            {t('先读一份真实样例')} <span aria-hidden="true">→</span>
          </Link>
        </div>
        <p className="trust-line">
          {t('有据可查的排盘')} <span>·</span> {t('读得懂的解读')} <span>·</span>{' '}
          {t('留给自己的选择')}
        </p>
      </div>
      <div
        className="observatory-art"
        role="img"
        aria-label={t('天体轨道装饰，不代表实际星体位置')}
      >
        <span className="art-caption">THE ART OF UNDERSTANDING YOURSELF</span>
        <svg viewBox="0 0 500 500" fill="none" aria-hidden="true">
          <g className="observatory-orbit" stroke="currentColor">
            <circle cx="250" cy="250" r="205" />
            <circle cx="250" cy="250" r="150" />
            <circle cx="250" cy="250" r="72" />
            <ellipse
              cx="250"
              cy="250"
              rx="225"
              ry="95"
              transform="rotate(-38 250 250)"
            />
            <path d="M45 250h410M250 45v410" opacity=".4" />
            <g fill="currentColor" stroke="none">
              <circle cx="125" cy="165" r="7" />
              <circle cx="385" cy="315" r="5" />
              <circle cx="214" cy="395" r="6" />
            </g>
          </g>
          <text
            x="250"
            y="269"
            textAnchor="middle"
            fill="currentColor"
            stroke="none"
            fontSize="58"
            fontFamily="serif"
          >
            观己
          </text>
        </svg>
        <p>
          {t('每一份排盘')}，
          <br />
          {t('都是一次重新认识自己的起点')}。
        </p>
        <Link
          className="art-link"
          to={ROUTES.baziNatal}
          aria-label={t('开始八字排盘')}
        >
          ↗
        </Link>
      </div>
    </section>
  );
}
