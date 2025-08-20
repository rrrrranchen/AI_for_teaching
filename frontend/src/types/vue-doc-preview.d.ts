// src/types/vue-doc-preview.d.ts
declare module "vue-doc-preview" {
  import { DefineComponent } from "vue";

  interface VueDocPreviewProps {
    value: string;
    type?: "office" | "pdf";
    style?: Record<string, string | number>;
    className?: string;
  }

  const VueDocPreview: DefineComponent<VueDocPreviewProps>;

  export default VueDocPreview;
}
