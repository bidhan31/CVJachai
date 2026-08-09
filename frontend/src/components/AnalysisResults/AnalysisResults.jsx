import React, { useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import html2canvas from 'html2canvas';
import { saveAs } from 'file-saver';
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx';
import { 
  ArrowLeft, 
  Sparkles, 
  Printer, 
  FileText, 
  Image as ImageIcon,
  CheckCircle2
} from 'lucide-react';

function AnalysisResults({ onBack, onBackToHome, data }) {
  const paperRef = useRef(null);

  // Fallback to demo data if nothing from API
  const rawMarkdown = data?.optimized_resume_markdown || "";
  // Strip outdated "References available upon request" line
  const resumeMarkdown = rawMarkdown
    .split('\n')
    .filter(line => !/references available upon request/i.test(line))
    .join('\n');
  const engine = data?.optimization_engine || "AI Core";
  const disclaimer = data?.disclaimer || "Please review for accuracy.";
  const recommendation = data?.recommendation || "";

  const handlePrint = () => {
    window.print();
  };

  const handleExportPNG = async () => {
    if (!paperRef.current) return;
    try {
      const canvas = await html2canvas(paperRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        logging: false,
      });
      canvas.toBlob((blob) => {
        saveAs(blob, 'optimized-resume.png');
      }, 'image/png');
    } catch (err) {
      alert('PNG export failed: ' + err.message);
    }
  };

  const handleExportDOCX = async () => {
    if (!resumeMarkdown) return;

    // Parse markdown lines into docx paragraphs
    const lines = resumeMarkdown.split('\n');
    const docParagraphs = [];

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) {
        docParagraphs.push(new Paragraph({ text: '' }));
        continue;
      }
      if (trimmed.startsWith('# ')) {
        docParagraphs.push(new Paragraph({
          text: trimmed.replace(/^#+\s*/, '').replace(/\*\*/g, ''),
          heading: HeadingLevel.HEADING_1,
        }));
      } else if (trimmed.startsWith('## ')) {
        docParagraphs.push(new Paragraph({
          text: trimmed.replace(/^#+\s*/, '').replace(/\*\*/g, ''),
          heading: HeadingLevel.HEADING_2,
        }));
      } else if (trimmed.startsWith('### ')) {
        docParagraphs.push(new Paragraph({
          text: trimmed.replace(/^#+\s*/, '').replace(/\*\*/g, ''),
          heading: HeadingLevel.HEADING_3,
        }));
      } else if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
        docParagraphs.push(new Paragraph({
          bullet: { level: 0 },
          children: [new TextRun(trimmed.replace(/^[*\-]\s*/, '').replace(/\*\*/g, '').replace(/\*/g, ''))],
        }));
      } else if (trimmed.startsWith('  * ') || trimmed.startsWith('  - ')) {
        docParagraphs.push(new Paragraph({
          bullet: { level: 1 },
          children: [new TextRun(trimmed.replace(/^\s*[*\-]\s*/, '').replace(/\*\*/g, '').replace(/\*/g, ''))],
        }));
      } else {
        // Strip markdown bold/italic
        const cleanText = trimmed.replace(/\*\*/g, '').replace(/\*/g, '').replace(/^#+\s*/, '');
        docParagraphs.push(new Paragraph({
          children: [new TextRun(cleanText)],
        }));
      }
    }

    const doc = new Document({
      sections: [{ properties: {}, children: docParagraphs }],
    });

    try {
      const blob = await Packer.toBlob(doc);
      saveAs(blob, 'optimized-resume.docx');
    } catch (err) {
      alert('DOCX export failed: ' + err.message);
    }
  };

  return (
    <div className="analysis-results-screen">
      <style>{`
        @media print {
          /* Reset everything to white */
          * { 
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          body, html {
            background: white !important;
            color: black !important;
          }
          /* Hide all app chrome */
          .app-container > * {
            display: none !important;
          }
          /* Only show the analysis results screen */
          .app-container > .analysis-results-screen {
            display: block !important;
            background: white !important;
            padding: 0 !important;
            margin: 0 !important;
          }
          /* Inside the screen, hide everything except the paper */
          .analysis-results-screen > * {
            display: none !important;
          }
          .analysis-results-screen > .container {
            display: block !important;
            background: white !important;
            margin: 0 !important;
            padding: 0 !important;
            max-width: 100% !important;
          }
          .container > * {
            display: none !important;
          }
          .container > .resume-paper-container {
            display: block !important;
            background: white !important;
            padding: 0 !important;
          }
          /* Paper itself */
          .resume-paper {
            box-shadow: none !important;
            border: none !important;
            margin: 0 !important;
            padding: 30px 40px !important;
            width: 100% !important;
            max-width: 100% !important;
            border-top: 4px solid #1e40af !important;
            background: white !important;
          }
          /* Skill chips stay readable */
          .skill-chip {
            border: 1px solid #bfdbfe !important;
            background: #eff6ff !important;
            color: #1e40af !important;
          }
        }
      `}</style>

      <div className="container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <a href="#" onClick={(e) => { e.preventDefault(); onBack(); }} className="back-link">
            <ArrowLeft size={18} />
            Back to Editor
          </a>
          <div className="logo" onClick={onBackToHome}>
            <div className="logo-icon">
              <Sparkles size={18} color="white" fill="white" />
            </div>
            <span>CVJACHAI</span>
          </div>
        </div>

        <div className="results-header">
          <div className="badge">
            <CheckCircle2 className="badge-icon" />
            Optimization Ready
          </div>
          <h1>Optimized ATS Resume</h1>
          <p className="section-subtitle">Tailored by High Performance AI for maximum impact</p>
        </div>

        <div className="export-actions" style={{ 
          display: 'flex', 
          gap: '15px', 
          marginBottom: '30px',
          justifyContent: 'center',
          flexWrap: 'wrap'
        }}>
          <button className="btn-action" onClick={handlePrint}>
            <Printer size={18} />
            Print to PDF
          </button>
          <button className="btn-action" onClick={handleExportDOCX}>
            <FileText size={18} />
            Download DOCX
          </button>
          <button className="btn-action" onClick={handleExportPNG}>
            <ImageIcon size={18} />
            Export PNG
          </button>
        </div>

        {recommendation && (
          <div className="recommendation-card" style={{
            background: 'rgba(34, 211, 238, 0.03)',
            border: '1px solid rgba(34, 211, 238, 0.15)',
            borderRadius: '16px',
            padding: '24px 30px',
            maxWidth: '860px',
            margin: '0 auto 30px auto',
            textAlign: 'left',
            display: 'flex',
            gap: '20px',
            alignItems: 'flex-start',
            boxShadow: '0 10px 30px -10px rgba(34, 211, 238, 0.15)',
            backdropFilter: 'blur(10px)',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              background: 'linear-gradient(90deg, rgba(34, 211, 238, 0.05) 0%, transparent 100%)',
              zIndex: -1
            }} />
            
            <div style={{
              background: 'rgba(34, 211, 238, 0.1)',
              color: 'var(--accent-cyan)',
              padding: '12px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <Sparkles size={24} style={{ filter: 'drop-shadow(0 0 4px var(--accent-cyan))' }} />
            </div>
            
            <div>
              <h3 style={{ 
                color: '#ffffff', 
                fontSize: '1.15rem', 
                fontWeight: '700', 
                marginBottom: '6px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
              }}>
                AI Recommendation
              </h3>
              <p style={{ 
                color: 'rgba(255, 255, 255, 0.8)', 
                fontSize: '0.975rem', 
                lineHeight: '1.6',
                margin: 0
              }}>
                {recommendation}
              </p>
            </div>
          </div>
        )}

        <div className="resume-paper-container" style={{ paddingBottom: '20px' }}>
          <div ref={paperRef} className="resume-paper" style={{
            background: '#ffffff',
            color: '#1a202c',
            padding: '60px 70px 40px 70px',
            borderRadius: '2px',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 20px 60px -15px rgba(0,0,0,0.4)',
            width: '100%',
            maxWidth: '860px',
            margin: '0 auto',
            textAlign: 'left',
            lineHeight: '1.6',
            fontFamily: "'Georgia', serif",
            borderTop: '5px solid #1e40af',
            position: 'relative'
          }}>
            <div className="markdown-content">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  td: ({children}) => (
                    <span className="skill-chip">{children}</span>
                  ),
                  tr: ({children}) => (
                    <span className="skill-chip-row">{children}</span>
                  ),
                  table: ({children}) => (
                    <div className="skills-chip-container">{children}</div>
                  ),
                  thead: ({children}) => null,
                  tbody: ({children}) => <>{children}</>,
                }}
              >{resumeMarkdown}</ReactMarkdown>
            </div>
          </div>

          {/* Disclaimer outside paper so it doesn't add extra print page */}
          <p style={{ 
            maxWidth: '860px',
            margin: '12px auto 0',
            padding: '10px 0',
            fontSize: '11px',
            color: 'rgba(255,255,255,0.35)',
            textAlign: 'center',
            fontStyle: 'italic'
          }}>
            {disclaimer}
          </p>
        </div>

        <div className="results-footer">
          <button className="btn-outline" onClick={onBack}>Optimize Another</button>
          <button className="btn-primary" onClick={onBackToHome} style={{ border: 'none', cursor: 'pointer' }}>Back to Home</button>
        </div>
      </div>
    </div>
  );
}

export default AnalysisResults;
