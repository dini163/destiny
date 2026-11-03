import { useState } from 'react';
import { useI18n } from '../../i18n/context';
const LOCAL_KEYS = ['destiny.personProfiles.v1', 'destiny.runeVault.v1'];
const SESSION_KEYS = ['report_input_r1', 'report_input_r2', 'report_input_r3'];
export function LocalDataControls() {
  const { t } = useI18n();
  const [confirming, setConfirming] = useState(false);
  // Store the message key (source Chinese), not the rendered string, so a
  // mid-dialog locale change still re-translates the notice on next render.
  const [notice, setNotice] = useState('');
  function exportData() {
    try {
      const entries = Object.fromEntries(
        LOCAL_KEYS.map((key) => [
          key,
          JSON.parse(localStorage.getItem(key) ?? '[]'),
        ]),
      );
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(entries, null, 2)], {
          type: 'application/json',
        }),
      );
      const a = document.createElement('a');
      a.href = url;
      a.download = 'destiny-local-data.json';
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice('导出文件可能含姓名、生辰与问题记录，请妥善保管。');
    } catch {
      setNotice('无法导出，请检查浏览器的存储权限。');
    }
  }
  function remove() {
    try {
      LOCAL_KEYS.forEach((key) => localStorage.removeItem(key));
      SESSION_KEYS.forEach((key) => sessionStorage.removeItem(key));
      window.location.reload();
    } catch {
      setNotice('清除未能完成，请使用浏览器的网站数据设置。');
    }
  }
  return (
    <details className="data-controls">
      <summary>{t('管理本机档案与收藏')}</summary>
      <p>
        {t('档案、卢恩收藏只存本机，没有自动加密或云端备份。清除会删除这些记录及当前报告输入，不会删除下载文件或浏览器历史。')}
      </p>
      <div className="local-data-options">
        <button className="btn-ghost" type="button" onClick={exportData}>
          {t('导出本机记录')}
        </button>
        <button
          className="btn-ghost"
          type="button"
          onClick={() => setConfirming(true)}
        >
          {t('清除本机记录')}
        </button>
      </div>
      {confirming && (
        <div className="local-data-notice" role="alert">
          <p>{t('请先导出需要保留的记录。确认清除所有本机档案和卢恩收藏？')}</p>
          <button className="btn-ghost" type="button" onClick={remove}>
            {t('确认清除')}
          </button>
          <button
            className="btn-ghost"
            type="button"
            onClick={() => setConfirming(false)}
          >
            {t('取消')}
          </button>
        </div>
      )}
      <p role="status">{notice ? t(notice) : ''}</p>
    </details>
  );
}
