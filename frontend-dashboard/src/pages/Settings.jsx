import { useState } from "react";
import { motion } from "framer-motion";
import { Key, Eye, EyeOff, Copy, Check, Palette, Code, RefreshCw } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ChatWidgetPreview } from "@/components/widget/ChatWidgetPreview";

// Récupération du token réel depuis les variables d'environnement
const REAL_TOKEN = import.meta.env.VITE_WIDGET_TOKEN || "pub_test_123456";

const colorPresets = [
  { name: "Bleu", value: "#2563eb" },
  { name: "Violet", value: "#7c3aed" },
  { name: "Vert", value: "#059669" },
  { name: "Rose", value: "#db2777" },
  { name: "Orange", value: "#ea580c" },
  { name: "Indigo", value: "#4f46e5" },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function Settings() {
  const [token] = useState(REAL_TOKEN);
  const [showToken, setShowToken] = useState(false);
  const [copied, setCopied] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [primaryColor, setPrimaryColor] = useState("#2563eb");
  const { toast } = useToast();

  const handleCopyToken = () => {
    navigator.clipboard.writeText(token);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast({ title: "Token copié", description: "Le token a été copié dans le presse-papier." });
  };

  const handleCopyCode = () => {
    // Code d'intégration généré dynamiquement
    const code = `<script
  src="https://askit-widget.vercel.app/widget.js"
  data-token="${token}"
  data-color="${primaryColor}"
  async>
</script>`;
    navigator.clipboard.writeText(code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
    toast({ title: "Code copié", description: "Le snippet a été copié." });
  };

  return (
    <DashboardLayout>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-8"
      >
        <motion.div variants={itemVariants}>
          <h1 className="text-3xl font-bold text-foreground">Réglages & Intégration</h1>
          <p className="text-muted-foreground mt-1">Configurez l'apparence et récupérez votre code d'installation.</p>
        </motion.div>

        <div className="grid gap-8 lg:grid-cols-2">
          <div className="space-y-6">
            {/* Token Card */}
            <motion.div variants={itemVariants}>
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Key className="h-5 w-5 text-primary" />
                    <CardTitle className="text-lg">Token API Public</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Input
                        type={showToken ? "text" : "password"}
                        value={token}
                        readOnly
                        className="pr-10 font-mono text-sm"
                      />
                      <button
                        onClick={() => setShowToken(!showToken)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                      >
                        {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    <Button variant="outline" size="icon" onClick={handleCopyToken}>
                      {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">Ce token identifie votre boutique de manière unique.</p>
                </CardContent>
              </Card>
            </motion.div>

            {/* Color Picker */}
            <motion.div variants={itemVariants}>
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Palette className="h-5 w-5 text-purple-500" />
                    <CardTitle className="text-lg">Couleur du Widget</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {colorPresets.map((color) => (
                      <button
                        key={color.value}
                        onClick={() => setPrimaryColor(color.value)}
                        className={`w-8 h-8 rounded-full transition-transform ${primaryColor === color.value ? 'ring-2 ring-offset-2 ring-primary scale-110' : ''}`}
                        style={{ backgroundColor: color.value }}
                      />
                    ))}
                    <input 
                      type="color" 
                      value={primaryColor} 
                      onChange={(e) => setPrimaryColor(e.target.value)}
                      className="w-8 h-8 rounded-full overflow-hidden border-0 p-0 cursor-pointer"
                    />
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Integration Code */}
            <motion.div variants={itemVariants}>
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Code className="h-5 w-5 text-blue-500" />
                    <CardTitle className="text-lg">Snippet HTML</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="relative bg-muted p-4 rounded-md font-mono text-xs overflow-x-auto">
                    <pre>{`<script
  src="https://askit-widget.vercel.app/widget.js"
  data-token="${token}"
  data-color="${primaryColor}"
  async>
</script>`}</pre>
                    <Button size="sm" variant="secondary" onClick={handleCopyCode} className="absolute top-2 right-2">
                      {copiedCode ? "Copié" : "Copier"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Preview */}
          <motion.div variants={itemVariants} className="lg:sticky lg:top-8">
            <Card className="h-full flex flex-col justify-center items-center bg-slate-50 border-dashed relative overflow-hidden min-h-[500px]">
               <div className="absolute inset-0 opacity-5 pointer-events-none bg-[url('https://ui.shadcn.com/placeholder.svg')] bg-repeat" />
               <p className="text-sm text-muted-foreground mb-4">Aperçu en temps réel</p>
               {/* Le composant de prévisualisation */}
               <ChatWidgetPreview primaryColor={primaryColor} />
            </Card>
          </motion.div>
        </div>
      </motion.div>
    </DashboardLayout>
  );
}