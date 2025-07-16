declare module "codemirror" {
  namespace CodeMirror {
    interface EditorConfiguration {
      mode?: string;
      theme?: string;
      lineNumbers?: boolean;
      autofocus: boolean;
      fontSize: string;
      // 其他配置项...
    }

    interface Editor {
      getValue(): string;
      setValue(value: string): void;
      focus(): void;
      isClean(): void;
      // 其他方法...
    }
  }

  function CodeMirror(
    host: HTMLElement | ((host: HTMLElement) => void),
    options?: CodeMirror.EditorConfiguration
  ): CodeMirror.Editor;

  export = CodeMirror;
}
