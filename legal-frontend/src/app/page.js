"use client";
import React, { useRef, useEffect, useState } from "react";
import { Scale, Send, Gavel, BookOpen, Search, Shield, AlertTriangle, FileText, Settings, ChevronRight, Loader2, Zap } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function Home() {
  const scrollRef = useRef(null);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState([]);

  // Danh sach cau hoi goi y phap luat
  const suggestions = [
    "Uống bia đi xe máy phạt bao nhiêu?",
    "Không đội mũ bảo hiểm bị xử lý thế nào?",
    "Vượt đèn đỏ mức phạt cao nhất?",
    "Đi ngược chiều xe máy phạt mấy tiền?"
  ];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async (text) => {
    const query = text || input;
    if (!query.trim() || isLoading) return;

    const userMsg = { role: "user", text: query };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      // Dynamic API URL resolution at runtime to avoid Next.js build-time environment variable traps.
      let api_host = "http://localhost:8000";
      if (typeof window !== "undefined") {
        const hostname = window.location.hostname;
        if (hostname !== "localhost" && hostname !== "127.0.0.1") {
          api_host = window.location.origin;
        }
      }
      const api_url = `${api_host}/chat`;
      
      const response = await fetch(api_url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query }),
      });
      const data = await response.json();
      
      // Server tra ve 2 truong rieng biet:
      // data.answer    = Chi co KET LUAN + CAN CU (do LLM viet)
      // data.reasoning = Nhat ky hop-by-hop THUAN TOAN tu Python, khong qua LLM
      const answer = data.answer || "";
      const reasoning = data.reasoning || "";
      
      setMessages((prev) => [...prev, { role: "assistant", text: answer, reasoning: reasoning }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", text: "⚠️ Lỗi kết nối đến hệ thống suy luận. Vui lòng thử lại.", reasoning: "" }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F1F5F9] p-6">
      {/* TOP NAVBAR */}
      <header className="flex items-center justify-between px-10 py-4 bg-gradient-to-r from-[#0B1020] via-[#111827] to-[#1E1B4B] rounded-2xl mb-6 shadow-[0_8px_32px_rgba(139,92,246,0.18)] backdrop-blur-xl">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-500/30">
              <Scale size={22} />
            </div>
            <div>
              <h1 className="text-lg font-black text-white tracking-tight">GENCORE</h1>
              <p className="text-[9px] font-bold text-blue-400 uppercase tracking-[0.3em]">Legal GraphRAG</p>
            </div>
          </div>

          <div className="h-6 w-[1px] bg-white/10 hidden sm:block"></div>

          <div className="hidden md:flex items-center gap-3 bg-white/5 border border-white/10 px-3 py-1.5 rounded-full">
            <div className="relative">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm border-2 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.5)]">
                <Gavel size={16} />
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-[#0B1020] animate-pulse"></div>
            </div>
            <span className="text-[11px] font-bold text-blue-400 uppercase tracking-[0.15em]">Agent Law</span>
          </div>
        </div>

        <div className="flex-1 max-w-xl mx-auto px-10">
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-blue-400 transition-colors">
              <Search size={18} />
            </div>
            <input
              type="text"
              placeholder="Tìm kiếm điều luật, nghị định..."
              className="w-full bg-white/5 border border-white/10 rounded-2xl py-2.5 pl-12 pr-4 text-sm text-white placeholder:text-slate-500 focus:bg-white/10 focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/10 outline-none transition-all duration-300"
            />
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button className="p-2 text-slate-400 hover:text-white transition-colors"><Settings size={20} /></button>
          <div className="flex items-center gap-3 pl-4 border-l border-white/10">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-bold text-white leading-none mb-1">Phuscbyboiz</p>
              <p className="text-[10px] text-slate-500 font-medium leading-none">Admin</p>
            </div>
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 p-0.5 shadow-lg">
              <img
                src="https://ui-avatars.com/api/?name=P&background=fff&color=0047FF&bold=true"
                className="w-full h-full rounded-full border border-black/20"
                alt="User"
              />
            </div>
          </div>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <div className="max-w-[1600px] mx-auto h-[calc(100vh-160px)] bg-white rounded-[40px] shadow-[0_20px_60px_rgba(0,0,0,0.12)] border border-slate-200 flex overflow-hidden">

        {/* SIDEBAR - Pháp luật Navigation */}
        <div className="w-72 bg-slate-900 flex flex-col p-6 border-r border-slate-800 shrink-0">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
              <BookOpen size={20} />
            </div>
            <div className="overflow-hidden">
              <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Cơ sở dữ liệu</h3>
              <p className="text-xs font-bold text-white truncate">Nghị định 168/2024</p>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-6 pr-2">
            {/* Danh muc luat */}
            <div>
              <div className="flex items-center justify-between mb-3 px-2">
                <h4 className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em]">Danh mục tra cứu</h4>
              </div>
              <div className="space-y-1.5">
                {[
                  { icon: "🏍️", label: "Xe mô tô, xe gắn máy", desc: "Điều 6 - NĐ168" },
                  { icon: "🚗", label: "Xe ô tô, xe tải", desc: "Điều 7 - NĐ168" },
                  { icon: "🚲", label: "Xe đạp, xe thô sơ", desc: "Điều 8 - NĐ168" },
                  { icon: "🚶", label: "Người đi bộ", desc: "Điều 9 - NĐ168" },
                  { icon: "👮", label: "Thẩm quyền xử phạt", desc: "Chương IV" },
                ].map((item, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(`Các lỗi vi phạm ${item.label}`)}
                    disabled={isLoading}
                    className="w-full text-left p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-blue-600/10 hover:border-blue-600/20 active:scale-[0.98] group transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-[11px] font-bold text-slate-300 group-hover:text-blue-400 transition-colors leading-tight">
                        {item.icon} {item.label}
                      </span>
                    </div>
                    <p className="text-[9px] text-slate-500 group-hover:text-slate-400 italic">{item.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Goi y nhanh */}
            <div className="pt-4 border-t border-white/5">
              <h4 className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 px-2">Gợi ý nhanh</h4>
              <div className="grid grid-cols-1 gap-2">
                {suggestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(q)}
                    disabled={isLoading}
                    className="text-[10px] text-left px-3 py-2 rounded-lg bg-white/5 text-slate-400 hover:text-white hover:bg-white/10 active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* CHAT AREA */}
        <div className="flex-1 flex flex-col bg-white min-w-0">
          {/* Header */}
          <div className="px-8 py-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <h2 className="text-sm font-black text-slate-800 uppercase tracking-tighter">Gencore Legal AI</h2>
              <span className="text-[9px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-bold">GraphRAG v2</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 bg-green-50 px-3 py-1 rounded-full">
                <Zap size={12} className="text-green-600" />
                <span className="text-[10px] font-bold text-green-700">Groq Llama 3.3</span>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-8 space-y-8">
            {/* Welcome Screen */}
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center gap-6 opacity-80">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-3xl flex items-center justify-center shadow-xl shadow-blue-500/20">
                  <Scale size={40} className="text-white" />
                </div>
                <div className="text-center">
                  <h2 className="text-2xl font-black text-slate-800 mb-2">Gencore Legal AI</h2>
                  <p className="text-sm text-slate-400 max-w-md">Hệ thống suy luận pháp luật trên Đồ thị tri thức. Hỏi bất kỳ câu hỏi nào về Nghị định 168/2024.</p>
                </div>
                <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
                  {suggestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(q)}
                      className="p-4 bg-slate-50 border border-slate-100 rounded-2xl text-left hover:bg-blue-50 hover:border-blue-200 transition-all group"
                    >
                      <p className="text-xs font-bold text-slate-700 group-hover:text-blue-700">{q}</p>
                      <div className="flex items-center gap-1 mt-2 text-slate-400 group-hover:text-blue-500">
                        <span className="text-[9px] font-bold">Hỏi ngay</span>
                        <ChevronRight size={12} />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Chat Messages */}
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                {/* Main message row */}
                <div className={`flex items-start gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 shadow-sm border ${
                    msg.role === 'user' ? 'bg-blue-100 border-blue-200' : 'bg-blue-600 border-blue-700 text-white'
                  }`}>
                    {msg.role === 'user' 
                      ? <img src="https://ui-avatars.com/api/?name=P&background=E0E7FF&color=4F46E5" alt="avatar" className="w-full h-full rounded-full" />
                      : <Gavel size={16} />
                    }
                  </div>
                  <div className={`max-w-[75%] px-6 py-4 rounded-[28px] ${
                    msg.role === 'user' 
                      ? 'bg-blue-600 text-white rounded-tr-none' 
                      : 'bg-slate-50 text-slate-700 border border-slate-100 rounded-tl-none shadow-sm'
                  }`}>
                    <div className="prose prose-sm max-w-none prose-slate">
                      <ReactMarkdown
                        components={{
                          p: ({node, ...props}) => <p className="mb-3 last:mb-0 leading-relaxed text-sm" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-bold text-blue-700 bg-blue-100/50 px-1 rounded" {...props} />,
                          h1: ({node, ...props}) => <h1 className="text-lg font-black text-slate-800 border-b-2 border-blue-200 pb-1 mb-4 mt-2" {...props} />,
                          h2: ({node, ...props}) => <h2 className="text-base font-bold text-blue-600 bg-blue-50 px-3 py-1 rounded-xl mb-3 mt-4 flex items-center gap-2" {...props} />,
                          h3: ({node, ...props}) => <h3 className="text-sm font-bold text-slate-700 mb-2 mt-3" {...props} />,
                          ul: ({node, ...props}) => <ul className="space-y-1.5 mb-4 list-none pl-0" {...props} />,
                          li: ({node, ...props}) => (
                            <li className="flex items-start gap-2 text-slate-600 text-sm">
                              <span className="text-blue-400 mt-0.5">✦</span>
                              <span {...props} />
                            </li>
                          ),
                          blockquote: ({node, ...props}) => (
                            <blockquote className="border-l-4 border-blue-400 bg-blue-50/30 p-3 rounded-r-xl my-4 italic text-slate-600" {...props} />
                          ),
                          code: ({node, ...props}) => (
                            <code className="bg-slate-100 text-pink-600 px-1.5 py-0.5 rounded font-mono text-[11px]" {...props} />
                          )
                        }}
                      >
                        {msg.text}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>

                {/* Reasoning Block - TACH RIENG ben ngoai bubble */}
                {msg.role === 'assistant' && msg.reasoning && (
                  <div className="ml-14 mt-3 max-w-[80%]">
                    <div className="bg-slate-900 rounded-2xl p-5 border border-slate-800 shadow-lg">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-5 h-5 bg-blue-600 rounded flex items-center justify-center">
                          <FileText size={12} className="text-white" />
                        </div>
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Graph Traversal Path</span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono leading-relaxed whitespace-pre-wrap">
                        <ReactMarkdown
                          components={{
                            p: ({node, ...props}) => <p className="mb-2 last:mb-0 leading-relaxed" {...props} />,
                            strong: ({node, ...props}) => <strong className="font-bold text-blue-400" {...props} />,
                            h3: ({node, ...props}) => <h3 className="text-xs font-bold text-slate-300 mb-2 mt-3 flex items-center gap-1" {...props} />,
                            ul: ({node, ...props}) => <ul className="space-y-1 mb-3 list-none pl-0" {...props} />,
                            li: ({node, ...props}) => (
                              <li className="flex items-start gap-2 text-slate-500 text-[11px]">
                                <span className="text-blue-500 mt-0.5 text-[8px]">→</span>
                                <span {...props} />
                              </li>
                            ),
                          }}
                        >
                          {msg.reasoning}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Loading */}
            {isLoading && (
              <div className="flex gap-3 items-center text-blue-600 font-bold text-xs animate-pulse">
                <Loader2 size={16} className="animate-spin" />
                <span>Gencore đang phân tích trên Đồ thị tri thức...</span>
              </div>
            )}
          </div>

          {/* Input Bar */}
          <div className="p-6 border-t border-slate-50">
            <div className="relative flex items-center bg-slate-50 border border-slate-200 rounded-2xl px-4 py-1 focus-within:border-blue-300 focus-within:ring-4 focus-within:ring-blue-100 transition-all">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Hỏi về luật giao thông, mức phạt, thẩm quyền..."
                className="flex-1 bg-transparent py-3.5 text-sm outline-none placeholder:text-slate-400"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || isLoading}
                className="p-2.5 bg-blue-600 text-white rounded-xl shadow-md hover:bg-blue-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95"
              >
                <Send size={18} />
              </button>
            </div>
            <p className="text-center mt-2 text-[9px] text-slate-400 font-medium">
              Hệ thống đang sử dụng Nghị định 168/2024/NĐ-CP • Dữ liệu có thể cần đối chiếu với văn bản gốc
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
