// frontend/app/layout.tsx
import "@mantine/core/styles.css";
import React from "react";
import { MantineProvider, ColorSchemeScript, createTheme, rem } from "@mantine/core";

export const metadata = {
  title: "AI 쇼츠 팩토리",
  description: "AI로 프리미엄 영상을 생성하세요",
};

// Premium Dark Theme Configuration
const theme = createTheme({
  colors: {
    // Custom Deep Blue/Purple semantic brand colors
    brand: [
      "#f3f0ff",
      "#e5dbff",
      "#d0bfff",
      "#b197fc",
      "#9775fa",
      "#845ef7", // Primary
      "#7950f2",
      "#7048e8",
      "#6741d9",
      "#5f3dc4",
    ],
    dark: [
      "#c1c2c5",
      "#A6A7AB",
      "#909296",
      "#5c5f66",
      "#373A40",
      "#2C2E33",
      "#25262b", // Surface
      "#1A1B1E", // Background
      "#141517",
      "#101113",
    ]
  },
  primaryColor: "brand",
  fontFamily: "Inter, sans-serif",
  // Glassmorphism components style overrides would go here
});

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <ColorSchemeScript />
      </head>
      <body>
        <MantineProvider theme={theme} defaultColorScheme="dark">
          {children}
        </MantineProvider>
      </body>
    </html>
  );
}
