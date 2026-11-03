import { Link } from 'react-router-dom';

import { PagePlaceholder } from '../components/layout/PagePlaceholder';
import { ROUTES } from '../nav';

/** Catch-all route for unknown paths — offers a way back to the portal. */
export function NotFoundPage() {
  return (
    <PagePlaceholder
      title="迷失星域"
      summary="未找到该路径对应的秘术体系，请返回测算大厅重新起盘。"
      status="ERROR 404"
      action={
        <Link to={ROUTES.overview} className="btn-primary">
          返回测算大厅
        </Link>
      }
    />
  );
}
