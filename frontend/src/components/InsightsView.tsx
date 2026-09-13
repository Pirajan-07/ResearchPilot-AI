import { PaperInsightsResponse } from "@/types/analysis";
import { 
  Target, 
  TestTube, 
  Database, 
  Award, 
  TrendingUp,
  Lightbulb,
  AlertTriangle,
  ChevronRight
} from "lucide-react";

export function InsightsView({ insights }: { insights: PaperInsightsResponse }) {
  const textSections = [
    { 
      id: "problem",
      title: "Core Problem", 
      content: insights.problem,
      icon: <Target className="w-5 h-5 text-rose-500" />
    },
    { 
      id: "methodology",
      title: "Methodological Insight", 
      content: insights.methodology,
      icon: <TestTube className="w-5 h-5 text-blue-500" />
    },
    { 
      id: "dataset",
      title: "Data Characteristics", 
      content: insights.dataset,
      icon: <Database className="w-5 h-5 text-cyan-500" />
    },
    { 
      id: "contribution",
      title: "Main Contribution", 
      content: insights.contribution,
      icon: <Award className="w-5 h-5 text-indigo-500" />
    },
    { 
      id: "future",
      title: "Future Trajectory", 
      content: insights.future_direction,
      icon: <TrendingUp className="w-5 h-5 text-violet-500" />
    },
  ];

  return (
    <div className="p-4 sm:p-8 overflow-y-auto h-full bg-slate-50/30">
      <div className="max-w-5xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between pb-4 border-b border-slate-200">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Deep Insights</h2>
            <p className="text-sm text-slate-500 mt-1">High-level analysis of the paper&apos;s core contributions and implications.</p>
          </div>
        </div>

        {/* Narrative Insights Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          {textSections.map((section, idx) => (
            <div 
              key={section.id} 
              className={`bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col ${idx === 4 ? 'md:col-span-2' : ''}`}
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

        {/* List-based Insights */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 pb-12 mt-6">
          
          {/* Key Findings */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col md:col-span-2 lg:col-span-1">
            <div className="bg-amber-50/50 px-5 py-3.5 border-b border-amber-100 flex items-center gap-3">
              <div className="p-1.5 bg-white rounded-md shadow-sm border border-amber-200">
                <Lightbulb className="w-5 h-5 text-amber-500" />
              </div>
              <h4 className="font-semibold text-amber-900 tracking-tight">Key Findings</h4>
            </div>
            <div className="p-5 flex-1">
              {insights.findings?.length > 0 ? (
                <ul className="space-y-3">
                  {insights.findings.map((finding, idx) => (
                    <li key={idx} className="flex items-start gap-2.5">
                      <ChevronRight className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <span className="text-[15px] text-slate-700 leading-relaxed">{finding}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-[15px] text-slate-400 italic">No specific findings extracted.</p>
              )}
            </div>
          </div>

          {/* Limitations */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col md:col-span-2 lg:col-span-1">
            <div className="bg-orange-50/50 px-5 py-3.5 border-b border-orange-100 flex items-center gap-3">
              <div className="p-1.5 bg-white rounded-md shadow-sm border border-orange-200">
                <AlertTriangle className="w-5 h-5 text-orange-500" />
              </div>
              <h4 className="font-semibold text-orange-900 tracking-tight">Identified Limitations</h4>
            </div>
            <div className="p-5 flex-1">
              {insights.limitations?.length > 0 ? (
                <ul className="space-y-3">
                  {insights.limitations.map((limitation, idx) => (
                    <li key={idx} className="flex items-start gap-2.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-orange-400 shrink-0 mt-2" />
                      <span className="text-[15px] text-slate-700 leading-relaxed">{limitation}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-[15px] text-slate-400 italic">No specific limitations extracted.</p>
              )}
            </div>
          </div>

        </div>
        
      </div>
    </div>
  );
}
