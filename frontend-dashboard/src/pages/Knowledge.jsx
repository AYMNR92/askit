import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BookOpen, Link as LinkIcon, FileText, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api"; // Notre utilitaire API

const Knowledge = () => {
  const { toast } = useToast();
  
  // États pour le texte manuel
  const [textInput, setTextInput] = useState("");
  const [isLearningText, setIsLearningText] = useState(false);

  // États pour le scraping URL
  const [urlInput, setUrlInput] = useState("");
  const [isScraping, setIsScraping] = useState(false);

  // --- FONCTION 1 : Apprendre du texte ---
  const handleTextSubmit = async (e) => {
    e.preventDefault();
    if (!textInput.trim()) return;

    setIsLearningText(true);
    try {
      await api.post("/api/learn", { text: textInput });
      
      toast({
        title: "Succès !",
        description: "Le texte a été ajouté à la base de connaissances.",
        variant: "default", // Vert par défaut dans Shadcn si configuré, sinon neutre
      });
      setTextInput("");
    } catch (error) {
      toast({
        title: "Erreur",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setIsLearningText(false);
    }
  };

  // --- FONCTION 2 : Scraper une URL ---
  const handleUrlSubmit = async (e) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setIsScraping(true);
    try {
      const result = await api.post("/api/scrape", { url: urlInput });
      
      toast({
        title: "Page aspirée !",
        description: result.message || "Le contenu de l'URL a été appris.",
      });
      setUrlInput("");
    } catch (error) {
      toast({
        title: "Échec de l'aspiration",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setIsScraping(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 animate-fade-in">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Base de Connaissances</h2>
          <p className="text-muted-foreground mt-2">
            Gérez les informations que votre IA utilise pour répondre aux clients.
          </p>
        </div>

        <Tabs defaultValue="text" className="w-full">
          <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
            <TabsTrigger value="text" className="gap-2">
              <FileText className="h-4 w-4" />
              Texte Manuel
            </TabsTrigger>
            <TabsTrigger value="url" className="gap-2">
              <LinkIcon className="h-4 w-4" />
              Site Web
            </TabsTrigger>
          </TabsList>

          {/* ONGLETS TEXTE MANUEL */}
          <TabsContent value="text" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Ajout Rapide</CardTitle>
                <CardDescription>
                  Copiez-collez des procédures, des horaires ou des FAQ directement ici.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleTextSubmit} className="space-y-4">
                  <Textarea
                    placeholder="Ex: Nos délais de livraison sont de 2 à 4 jours ouvrés..."
                    className="min-h-[200px]"
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                  />
                  <Button type="submit" disabled={isLearningText}>
                    {isLearningText ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Enregistrement...</>
                    ) : (
                      <><BookOpen className="mr-2 h-4 w-4" /> Apprendre ce texte</>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ONGLET URL */}
          <TabsContent value="url" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Aspirateur de Site Web</CardTitle>
                <CardDescription>
                  Entrez l'URL d'une page publique (Blog, Documentation, Produit) pour l'analyser.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleUrlSubmit} className="space-y-4">
                  <div className="flex gap-4">
                    <Input
                      placeholder="https://monsite.com/faq"
                      value={urlInput}
                      onChange={(e) => setUrlInput(e.target.value)}
                      type="url"
                    />
                    <Button type="submit" disabled={isScraping}>
                      {isScraping ? (
                        <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyse...</>
                      ) : (
                        "Scanner"
                      )}
                    </Button>
                  </div>
                  <div className="text-sm text-muted-foreground bg-muted/50 p-4 rounded-lg">
                    <p className="font-medium mb-1">💡 Note :</p>
                    L'IA va découper la page en petits morceaux pour mieux comprendre le contexte. 
                    Cela consomme votre quota de tokens.
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};

export default Knowledge;