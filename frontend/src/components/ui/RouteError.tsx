import { Link, useRouteError } from 'react-router-dom';
import { ROUTES } from '../../nav';
export function RouteError() {
  const error = useRouteError();
  const missingChunk =
    error instanceof Error &&
    /dynamically imported|Loading chunk|module script/i.test(error.message);
  return (
    <main className="route-error" role="alert">
      <h1>
        {missingChunk ? '页面刚刚更新，请重新载入。' : '这个页面暂时无法打开。'}
      </h1>
      <p>已保存的本机档案不会因此删除。你可以重试，或回到首页继续探索。</p>
      <div>
        <button
          type="button"
          className="btn-primary"
          onClick={() => window.location.reload()}
        >
          重新载入
        </button>
        <Link className="btn-ghost" to={ROUTES.overview}>
          回到首页
        </Link>
      </div>
    </main>
  );
}
