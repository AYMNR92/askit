import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare, User, Bot, Calendar, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

const Conversations = () => {
  const [conversations, setConversations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Charger l'historique au montage
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await api.get("/api/history");
        setConversations(data || []);
      } catch (err) {
        setError("Impossible de charger l'historique.");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchHistory();
  }, []);

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Historique</h2>
            <p className="text-muted-foreground mt-2">
              Retrouvez toutes les interactions entre vos clients et l'IA.
            </p>
          </div>
          <Badge variant="outline" className="px-4 py-1">
            {conversations.length} Conversations
          </Badge>
        </div>

        {isLoading ? (
          <div className="flex justify-center p-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : error ? (
          <div className="text-red-500 bg-red-50 p-4 rounded-lg border border-red-100">
            {error}
          </div>
        ) : conversations.length === 0 ? (
          <Card className="bg-muted/50 border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <MessageSquare className="h-12 w-12 mb-4 opacity-20" />
              <p>Aucune conversation enregistrée pour le moment.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {conversations.map((conv) => (
              <Card key={conv.id} className="overflow-hidden hover:shadow-md transition-shadow">
                <CardHeader className="bg-muted/30 py-3 flex flex-row items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="h-3 w-3" />
                    {new Date(conv.created_at).toLocaleString()}
                  </div>
                  <span className="text-xs font-mono text-muted-foreground">ID: {conv.id.slice(0,8)}</span>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="flex flex-col divide-y">
                    {/* On suppose que conv.messages est un tableau d'objets {role, content} */}
                    {/* Si Supabase stocke du JSONB, c'est direct. Si c'est du texte, il faut parser. */}
                    {(Array.isArray(conv.messages) ? conv.messages : JSON.parse(conv.messages || '[]')).map((msg, idx) => (
                      <div 
                        key={idx} 
                        className={`p-4 flex gap-4 ${msg.role === 'bot' ? 'bg-slate-50' : 'bg-white'}`}
                      >
                        <div className={`mt-1 p-2 rounded-full h-fit ${msg.role === 'bot' ? 'bg-primary/10 text-primary' : 'bg-gray-100 text-gray-600'}`}>
                          {msg.role === 'bot' ? <Bot size={16} /> : <User size={16} />}
                        </div>
                        <div className="flex-1 space-y-1">
                          <p className="text-sm font-medium">
                            {msg.role === 'bot' ? 'Assistant IA' : 'Visiteur'}
                          </p>
                          <p className="text-sm text-foreground/90 whitespace-pre-wrap">
                            {msg.content}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default Conversations;