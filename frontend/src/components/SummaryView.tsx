import { PaperSummaryResponse } from "@/types/analysis";
import { 
  BookOpen, 
  Target, 
  Crosshair, 
  TestTube, 
  Database, 
  Lightbulb, 
  AlertTriangle, 
  CheckSquare, 
  TrendingUp 
} from "lucide-react";

export function SummaryView({ summary }: { summary: PaperSummaryResponse }) {
  const sections = [
    { 
      id: "overview",
      title: "Overview", 
      content: summary.overview,
      icon: <BookOpen className="w-5 h-5 text-indigo-500" />,
      colSpan: "md:col-span-2" 
    },
    { 
      id: "problem",
      title: "Problem Statement", 
      content: summary.problem,
      icon: <Target className="w-5 h-5 text-rose-500" />
    },
    { 
      id: "objectives",
      title: "Objectives", 
      content: summary.objectives,
      icon: <Crosshair className="w-5 h-5 text-emerald-500" />
    },
    { 
      id: "methodology",
      title: "Methodology", 
      content: summary.methodology,
      icon: <TestTube className="w-5 h-5 text-blue-500" />
    },
    { 
      id: "dataset",
      title: "Dataset", 
      content: summary.dataset,
      icon: <Database className="w-5 h-5 text-cyan-500" />
    },
    { 
      id: "findings",
      title: "Key Findings", 
      content: summary.findings,
      icon: <Lightbulb className="w-5 h-5 text-amber-500" />
    },
    { 
      id: "limitations",
      title: "Limitations", 
      content: summary.limitations,
      icon: <AlertTriangle className="w-5 h-5 text-orange-500" />
    },
    { 
      id: "conclusion",
      title: "Conclusion", 
      content: summary.conclusion,
      icon: <CheckSquare className="w-5 h-5 text-green-600" />,
      colSpan: "md:col-span-2"
    },
    { 
      id: "future",
      title: "Future Direction", 
      content: summary.future_direction,
      icon: <TrendingUp className="w-5 h-5 text-violet-500" />,
      colSpan: "md:col-span-2"
    },
  ];

  return (
    <div className="p-4 sm:p-8 overflow-y-auto h-full bg-slate-50/30">
      <div className="max-w-5xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between pb-4 border-b border-slate-200">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Structured Summary</h2>
            <p className="text-sm text-slate-500 mt-1">AI-generated comprehensive breakdown of the paper.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 pb-12">
          {sections.map((section) => (
            <div 
              key={section.id} 
              className={`bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col ${section.colSpan || ''}`}
            >
              <div className="bg-slate-50/80 px-5 py-3.5 border-b border-slate-100 flex items-center gap-3">
                <div className="p-1.5 bg-white rounded-md shadow-sm border border-slate-200/60">
                  {section.icon}
                </div>
                <h4 className="font-semibold text-slate-900 tracking-tight">{section.title}</h4>
              </div>
              <div className="p-5 flex-1">
                <p className="text-[15px] text-slate-700 leading-relaxed">
                  {section.content || <span className="text-slate-400 italic">Not explicitly identified in the text.</span>}
                </p>
              </div>
            </div>
          ))}
        </div>
        
      </div>
    </div>
  );
}
