import React, { useEffect, useMemo, useState } from "react";

import { API_BASE } from "../constants";
import { api } from "../services/api";

function toAbsoluteDrawingUrl(drawingPath) {
  if (!drawingPath) {
    return "";
  }
  if (drawingPath.startsWith("http://") || drawingPath.startsWith("https://")) {
    return drawingPath;
  }
  return `${API_BASE}${drawingPath}`;
}

function buildViewerUrl(drawingPath, page, zoom, fitWidth) {
  const base = toAbsoluteDrawingUrl(drawingPath);
  if (!base) {
    return "";
  }

  const params = [`page=${page}`];
  if (fitWidth) {
    params.push("view=FitH");
  } else {
    params.push(`zoom=${zoom}`);
  }
  return `${base}#${params.join("&")}`;
}

export default function PdfDrawingViewer({ activeJob, operatorId, onStatus, refreshAll }) {
  const [drawingPath, setDrawingPath] = useState("");
  const [page, setPage] = useState(1);
  const [zoom, setZoom] = useState(125);
  const [fitWidth, setFitWidth] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setDrawingPath("");
    setPage(1);
    setZoom(125);
    setFitWidth(true);
    setError("");
  }, [activeJob?.job_id]);

  const viewerUrl = useMemo(() => buildViewerUrl(drawingPath, page, zoom, fitWidth), [drawingPath, page, zoom, fitWidth]);

  async function handleOpenDrawing() {
    if (!activeJob?.job_id) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await api.openDrawing(activeJob.job_id, operatorId);
      const openedPath = response?.data?.drawing_url || response?.data?.drawing_file || activeJob.drawing_file || "";
      if (!openedPath) {
        throw new Error("No drawing path was returned by backend.");
      }

      setDrawingPath(openedPath);
      setPage(1);
      setFitWidth(true);

      if (onStatus) {
        onStatus(`Drawing opened for ${activeJob.job_id}`);
      }
      if (refreshAll) {
        await refreshAll();
      }
    } catch (openError) {
      const message = openError instanceof Error ? openError.message : "Failed to open drawing";
      setError(message);
      if (onStatus) {
        onStatus(`Open drawing failed: ${message}`);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="pdf-viewer">
      <div className="pdf-toolbar">
        <button type="button" onClick={handleOpenDrawing} disabled={!activeJob || loading}>
          {loading ? "Opening..." : "Open Drawing"}
        </button>
        <button type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={!drawingPath || page <= 1}>
          Prev Page
        </button>
        <button type="button" onClick={() => setPage((current) => current + 1)} disabled={!drawingPath}>
          Next Page
        </button>
        <button
          type="button"
          onClick={() => {
            setFitWidth(false);
            setZoom((current) => Math.max(50, current - 25));
          }}
          disabled={!drawingPath}
        >
          Zoom -
        </button>
        <button
          type="button"
          onClick={() => {
            setFitWidth(false);
            setZoom((current) => Math.min(300, current + 25));
          }}
          disabled={!drawingPath}
        >
          Zoom +
        </button>
        <button type="button" onClick={() => setFitWidth(true)} disabled={!drawingPath}>
          Fit Width
        </button>
      </div>

      <div className="pdf-meta">
        <span>
          <strong>File:</strong> {drawingPath || activeJob?.drawing_file || "-"}
        </span>
        <span>
          <strong>Page:</strong> {page}
        </span>
        <span>
          <strong>Zoom:</strong> {fitWidth ? "Fit Width" : `${zoom}%`}
        </span>
      </div>

      {error ? <p className="message">{error}</p> : null}

      {viewerUrl ? (
        <iframe className="pdf-frame" src={viewerUrl} title="Technical drawing PDF viewer" />
      ) : (
        <div className="pdf-placeholder">Open a drawing to display the PDF here.</div>
      )}
    </div>
  );
}
