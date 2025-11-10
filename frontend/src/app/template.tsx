// frontend/src/app/template.tsx
"use client";

import { motion } from "framer-motion";
import { usePathname } from "next/navigation";

export default function Template({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <motion.div
      // ページごとにユニークなkeyを与えることが重要
      key={pathname}
      // ページが表示されるときのアニメーション
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      // ページが消えるときのアニメーション
      exit={{ opacity: 0, y: 15 }}
      transition={{ type: "tween", ease: "easeInOut", duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}
