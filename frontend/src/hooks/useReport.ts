import {
  fetchReportByLink,
  fetchReportDocument,
  fetchReportPreview,
} from '../api/report';
import type { ApiError } from '../api/client';
import type { ReportDocument, ReportPreview, ReportProduct } from '../types/report';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * Report page state: preview → generate → full document.
 *
 * The report page is entered with a pending input (handed over from the chart
 * pages via sessionStorage), then walks preview → full report. The three
 * mutations all go through {@link useLastSuccessMutation}, so the previous view
 * stays on screen while the next request is in flight instead of flashing blank.
 */
export function useReport() {
  const previewMutation = useLastSuccessMutation<
    ReportPreview,
    ApiError,
    { product: ReportProduct; input: unknown }
  >(({ product, input }) => fetchReportPreview(product, input));

  const documentMutation = useLastSuccessMutation<
    ReportDocument,
    ApiError,
    { product: ReportProduct; input: unknown }
  >(({ product, input }) => fetchReportDocument(product, input));

  const fetchMutation = useLastSuccessMutation<
    ReportDocument,
    ApiError,
    { product: ReportProduct; orderId: string; token: string; input: unknown }
  >(({ product, orderId, token, input }) => fetchReportByLink(product, orderId, token, input));

  return {
    preview: previewMutation.data,
    document: documentMutation.data,
    previewError: previewMutation.error,
    generateError: documentMutation.error,
    fetchError: fetchMutation.error,
    isPreviewPending: previewMutation.isPending,
    isGenerating: documentMutation.isPending,
    requestPreview: (product: ReportProduct, input: unknown) =>
      previewMutation.mutate({ product, input }),
    generate: (product: ReportProduct, input: unknown) =>
      documentMutation.mutate({ product, input }),
    fetchByLink: (product: ReportProduct, orderId: string, token: string, input: unknown) =>
      fetchMutation.mutate({ product, orderId, token, input }),
  };
}
