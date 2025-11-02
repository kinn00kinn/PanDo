import { User } from "lucide-react";

type Props = {
  sizePx?: number; // ピクセルサイズで指定 (例: 40)
};

export default function UserIcon({ sizePx = 40 }: Props) {
  return (
    <div
      className="flex-shrink-0 rounded-full border-2 border-black flex items-center justify-center bg-white"
      style={{ width: `${sizePx}px`, height: `${sizePx}px` }}
    >
      <User size={sizePx * 0.6} className="text-black" />
    </div>
  );
}