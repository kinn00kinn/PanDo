"use client";

import { motion, Variants } from "framer-motion";
import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";

// 1. タイムライン用のアニメーション定義 (スライドなし・フェードのみ)
const timelineVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

// 2. 記事詳細ページ用のアニメーション定義 (下から上へスライド)
const articleDetailVariants: Variants = {
  initial: {
    opacity: 0,
    y: "100vh", // 画面の高さ分、下から
  },
  animate: {
    opacity: 1,
    y: "0vh", // 画面中央へ
  },
  exit: {
    opacity: 0,
    y: "100vh", // 下へ戻る
  },
};

// 3. その他のページ用 (フェード)
const defaultVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

export default function Template({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // スクロール位置リセット用のRef
  const mainRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // 新しいページがタイムライン('/') *ではない* 場合 (
    // (例: /article/... や /profile などに遷移した場合) のみ、
    // スクロールをトップに戻します。
    if (pathname !== "/" && mainRef.current) {
      mainRef.current.scrollTop = 0;
    }
    // pathname が '/' (タイムライン) に戻ってきた場合は何もしません。
    // これにより、ブラウザが記憶しているスクロール位置が保持されます。
  }, [pathname]);

  // ★ 4. pathname に基づいて適用するアニメーションを選択
  let selectedVariants: Variants;
  if (pathname === "/") {
    // タイムラインページの場合
    selectedVariants = timelineVariants;
  } else if (pathname.startsWith("/article/")) {
    // 記事詳細ページの場合
    selectedVariants = articleDetailVariants;
  } else {
    // /links や /profile などの他のページ
    selectedVariants = defaultVariants;
  }

  return (
    <motion.div
      ref={mainRef}
      key={pathname}
      // ★ 5. 選択したアニメーションを適用
      variants={selectedVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      // アニメーションの速度
      transition={{ type: "tween", ease: "easeInOut", duration: 0.4 }}
    >
      {children}
    </motion.div>
  );
}
