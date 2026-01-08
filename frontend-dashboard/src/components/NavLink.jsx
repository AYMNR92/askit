import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

export function NavLink({ 
  to, 
  children, 
  className, 
  activeClassName, 
  end = false,
  ...props 
}) {
  const location = useLocation();
  const isActive = end 
    ? location.pathname === to 
    : location.pathname.startsWith(to);

  return (
    <Link
      to={to}
      className={cn(className, isActive && activeClassName)}
      {...props}
    >
      {children}
    </Link>
  );
}
