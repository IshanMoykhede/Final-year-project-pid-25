import React, { useEffect, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import type { RetrievedClause } from '../../api/chat';

pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;

type PdfBox = Record<string, unknown>;

interface DocumentPdfViewerProps {
  url: string;
  selectedClause?: RetrievedClause | null;
}

interface RenderedPage {
  pageNumber: number;
  width: number;
  height: number;
  canvas: HTMLCanvasElement;
}

const numberValue = (box: PdfBox, keys: string[]): number | null => {
  for (const key of keys) {
    const value = box[key];
    if (typeof value === 'number') return value;
    if (typeof value === 'string' && value.trim() && Number.isFinite(Number(value))) return Number(value);
  }
  return null;
};

const getBoxStyle = (box: PdfBox, pageWidth: number, pageHeight: number): React.CSSProperties | null => {
  const rawX = numberValue(box, ['x', 'left', 'x0']);
  const rawY = numberValue(box, ['y', 'top', 'y0']);
  const rawWidth = numberValue(box, ['w', 'width']);
  const rawHeight = numberValue(box, ['h', 'height']);
  const x1 = numberValue(box, ['x1', 'right']);
  const y1 = numberValue(box, ['y1', 'bottom']);

  if (rawX === null || rawY === null) return null;
  const width = rawWidth ?? (x1 === null ? null : x1 - rawX);
  const height = rawHeight ?? (y1 === null ? null : y1 - rawY);
  if (width === null || height === null || width <= 0 || height <= 0) return null;

  const isNormalized = Math.max(rawX, rawY, width, height) <= 1.01;
  const x = isNormalized ? rawX * pageWidth : rawX;
  const y = isNormalized ? rawY * pageHeight : rawY;
  const boxWidth = isNormalized ? width * pageWidth : width;
  const boxHeight = isNormalized ? height * pageHeight : height;

  return {
    left: `${(x / pageWidth) * 100}%`,
    top: `${(y / pageHeight) * 100}%`,
    width: `${(boxWidth / pageWidth) * 100}%`,
    height: `${(boxHeight / pageHeight) * 100}%`,
  };
};

export const DocumentPdfViewer: React.FC<DocumentPdfViewerProps> = ({ url, selectedClause }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [pages, setPages] = useState<RenderedPage[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    const loadPdf = async () => {
      setError('');
      setPages([]);
      try {
        const pdf = await pdfjsLib.getDocument(url).promise;
        const renderedPages: RenderedPage[] = [];
        for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
          const page = await pdf.getPage(pageNumber);
          const baseViewport = page.getViewport({ scale: 1 });
          const viewport = page.getViewport({ scale: 1.35 });
          const canvas = document.createElement('canvas');
          canvas.width = viewport.width;
          canvas.height = viewport.height;
          await page.render({ canvasContext: canvas.getContext('2d')!, viewport }).promise;
          renderedPages.push({
            pageNumber,
            width: baseViewport.width,
            height: baseViewport.height,
            canvas,
          });
        }
        if (!cancelled) setPages(renderedPages);
      } catch (loadError) {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : 'Unable to render this PDF.');
      }
    };
    void loadPdf();
    return () => { cancelled = true; };
  }, [url]);

  useEffect(() => {
    if (!selectedClause || !containerRef.current) return;
    const firstBox = selectedClause.bbox.find((box) => {
      const pageNumber = numberValue(box, ['page_number', 'page']);
      return pageNumber !== null;
    });
    const pageNumber = firstBox ? numberValue(firstBox, ['page_number', 'page']) : null;
    const target = pageNumber ? containerRef.current.querySelector(`[data-page-number="${pageNumber}"]`) : null;
    target?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [selectedClause]);

  if (error) return <div className="flex min-h-[320px] items-center justify-center rounded-lg bg-red-50 p-6 text-center text-sm text-red-700">{error}</div>;
  if (!pages.length) return <div className="flex min-h-[520px] items-center justify-center text-sm text-gray-500">Rendering document...</div>;

  return (
    <div ref={containerRef} className="max-h-[700px] space-y-4 overflow-auto rounded-lg bg-slate-200 p-3">
      {pages.map((page) => {
        const boxes = selectedClause?.bbox.filter((box) => numberValue(box, ['page_number', 'page']) === page.pageNumber) ?? [];
        return (
          <div key={page.pageNumber} data-page-number={page.pageNumber} className="relative mx-auto w-fit shadow-md">
            <img src={page.canvas.toDataURL()} alt={`Page ${page.pageNumber}`} className="block max-w-full" />
            {boxes.map((box, index) => {
              const style = getBoxStyle(box, page.width, page.height);
              return style ? <div key={`${page.pageNumber}-${index}`} className="pointer-events-none absolute border-2 border-amber-400 bg-amber-300/30 shadow-[0_0_0_3px_rgba(251,191,36,0.18)]" style={style} /> : null;
            })}
            <span className="absolute bottom-1 right-2 rounded bg-black/60 px-1.5 py-0.5 text-[10px] text-white">{page.pageNumber}</span>
          </div>
        );
      })}
    </div>
  );
};
