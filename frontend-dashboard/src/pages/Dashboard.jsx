import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { MessageSquare, Bot, Clock, Users, ArrowUpRight, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { api } from "@/lib/api";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const [stats, setStats] = useState({
    conversations: 0,
    responses: 0
  });

  useEffect(() => {
    // On récupère l'historique pour calculer les vraies stats
    const fetchStats = async () => {
      try {
        const history = await api.get("/api/history");
        setStats({
          conversations: history.length,
          responses: history.reduce((acc, curr) => acc + (curr.messages ? JSON.parse(curr.messages).length : 0), 0)
        });
      } catch (e) {
        console.error("Erreur stats", e);
      }
    };
    fetchStats();
  }, []);

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Vue d'ensemble</h1>
          <p className="text-muted-foreground">Vos statistiques en temps réel.</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Conversations Totales</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.conversations}</div>
              <p className="text-xs text-muted-foreground">+100% depuis le début</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Messages Échangés</CardTitle>
              <Bot className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.responses}</div>
              <p className="text-xs text-muted-foreground">Interactions totales</p>
            </CardContent>
          </Card>
          
          {/* Cartes statiques pour le moment */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Temps de réponse</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">~2s</div>
              <p className="text-xs text-muted-foreground">Moyenne estimée</p>
            </CardContent>
          </Card>
        </div>

        <Card className="bg-gradient-to-r from-violet-500/10 to-purple-500/10 border-0">
          <CardContent className="p-6 flex items-center justify-between">
            <div className="flex gap-4 items-center">
               <div className="p-3 bg-primary/20 rounded-full text-primary">
                 <Sparkles size={24} />
               </div>
               <div>
                 <h3 className="font-bold text-lg">Améliorez votre IA</h3>
                 <p className="text-muted-foreground">Ajoutez des connaissances pour rendre votre bot plus intelligent.</p>
               </div>
            </div>
            <Link to="/knowledge">
              <Button>Entraîner l'IA</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}