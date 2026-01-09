import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, X, Send, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

const mockMessages = [
  { role: "bot", content: "Bonjour ! Comment puis-je vous aider ?" },
  { role: "user", content: "Quels sont vos délais de livraison ?" },
  { role: "bot", content: "Nous livrons généralement sous 24 à 48h ouvrées." },
];

export function ChatWidgetPreview({ primaryColor = "#2563eb" }) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="relative z-10 font-sans">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="absolute bottom-16 right-0 w-[300px] bg-white rounded-xl shadow-xl border overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 text-white flex justify-between items-center" style={{ backgroundColor: primaryColor }}>
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5" />
                <span className="font-medium">Support Client</span>
              </div>
              <X className="w-4 h-4 cursor-pointer" onClick={() => setIsOpen(false)} />
            </div>

            {/* Messages */}
            <div className="h-[250px] bg-slate-50 p-4 space-y-3 overflow-y-auto">
              {mockMessages.map((msg, i) => (
                <div key={i} className={cn("flex", msg.role === 'user' ? "justify-end" : "justify-start")}>
                  <div 
                    className={cn("max-w-[85%] p-3 text-sm rounded-lg", msg.role === 'user' ? "text-white" : "bg-white border text-slate-800")}
                    style={msg.role === 'user' ? { backgroundColor: primaryColor } : {}}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>

            {/* Input */}
            <div className="p-3 bg-white border-t flex gap-2">
              <div className="flex-1 bg-slate-100 rounded-full px-3 py-2 text-sm text-slate-400">Posez une question...</div>
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-white" style={{ backgroundColor: primaryColor }}>
                <Send className="w-4 h-4" />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="w-12 h-12 rounded-full flex items-center justify-center text-white shadow-lg absolute bottom-0 right-0"
        style={{ backgroundColor: primaryColor }}
      >
        {isOpen ? <X className="w-6 h-6" /> : <MessageCircle className="w-6 h-6" />}
      </motion.button>
    </div>
  );
}