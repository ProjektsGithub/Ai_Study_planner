/**
 * usePdfExport — Hook réutilisable pour l'export PDF d'un plan d'étude
 * Appelle /api/v1/exports/plans/{planId}/pdf et déclenche un téléchargement automatique
 */
import { useState, useCallback } from 'react';
import apiClient from '../api/client';

/**
 * @returns {{ exportPdf: Function, exporting: boolean, exportError: string|null }}
 */
const usePdfExport = () => {
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState(null);

  const exportPdf = useCallback(async (planId, filename) => {
    if (!planId) return;
    setExporting(true);
    setExportError(null);

    try {
      const response = await apiClient.post(
        `/api/v1/exports/plans/${planId}/pdf`,
        {},
        { responseType: 'blob' }
      );

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || `plan_etude_${planId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setExportError(
        typeof detail === 'string' ? detail : 'Erreur lors de la génération du PDF.'
      );
    } finally {
      setExporting(false);
    }
  }, []);

  return { exportPdf, exporting, exportError };
};

export default usePdfExport;
