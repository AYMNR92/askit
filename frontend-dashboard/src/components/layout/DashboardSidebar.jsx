import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  MessageSquare,
  BookOpen,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { api } from "@/lib/api";

const navItems = [
  { title: "Vue d'ensemble", href: "/", icon: LayoutDashboard },
  { title: "Conversations", href: "/conversations", icon: MessageSquare },
  { title: "Connaissances", href: "/knowledge", icon: BookOpen },
  { title: "Réglages", href: "/settings", icon: Settings },
];

export function DashboardSidebar({ className }) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const [quota, setQuota] = useState({ used: 0, limit: 1000 });

  // Simulation de récupération du quota (À connecter plus tard à /api/me)
  useEffect(() => {
    // Pour l'instant, on laisse statique ou on peut baser ça sur le nombre de messages
    // const fetchQuota = async () => ...
  }, []);

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 80 : 280 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className={cn(
        "relative flex flex-col bg-card border-r border-border h-screen sticky top-0",
        className
      )}
    >
      {/* Logo & Toggle */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <motion.div
          initial={false}
          animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
          className="overflow-hidden"
        >
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">AS</span>
            </div>
            <span className="font-semibold text-foreground whitespace-nowrap">
              Askit Admin
            </span>
          </Link>
        </motion.div>
        
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className="h-8 w-8 shrink-0 ml-auto"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                "hover:bg-muted/50",
                isActive && "bg-primary/10 text-primary font-medium",
                !isActive && "text-muted-foreground hover:text-foreground"
              )}
            >
              <item.icon className={cn("h-5 w-5 shrink-0", isActive && "text-primary")} />
              <motion.span
                initial={false}
                animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
                className="overflow-hidden whitespace-nowrap"
              >
                {item.title}
              </motion.span>
            </Link>
          );
        })}
      </nav>

      {/* Credits / Quota */}
      <motion.div
        initial={false}
        animate={{ opacity: collapsed ? 0 : 1, height: collapsed ? 0 : "auto" }}
        className="overflow-hidden px-4 pb-4"
      >
        <div className="p-3 rounded-lg bg-muted/30 border border-border/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-muted-foreground">Utilisation</span>
            <span className="text-xs text-foreground font-semibold">Standard</span>
          </div>
          <Progress value={33} className="h-1.5" />
          <p className="text-xs text-muted-foreground mt-2">
            Plan Free actif
          </p>
        </div>
      </motion.div>

      {/* User Profile */}
      <div className="p-3 border-t border-border">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className={cn(
                "flex items-center gap-3 w-full p-2 rounded-lg hover:bg-muted/50 transition-colors",
                collapsed && "justify-center"
              )}>
              <Avatar className="h-8 w-8 shrink-0">
                <AvatarFallback className="bg-primary/10 text-primary text-sm">AD</AvatarFallback>
              </Avatar>
              <motion.div
                initial={false}
                animate={{ opacity: collapsed ? 0 : 1, width: collapsed ? 0 : "auto" }}
                className="overflow-hidden text-left"
              >
                <p className="text-sm font-medium text-foreground truncate">Administrateur</p>
                <p className="text-xs text-muted-foreground truncate">admin@askit.com</p>
              </motion.div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuItem className="text-destructive">
              <LogOut className="h-4 w-4 mr-2" />
              Déconnexion
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </motion.aside>
  );
}