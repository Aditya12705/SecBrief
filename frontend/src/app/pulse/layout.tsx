import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SecBrief Pulse",
};

export default function PulseLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
