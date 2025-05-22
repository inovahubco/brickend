import ejs from 'ejs';
import { readFileSync } from 'fs';
import { join } from 'path';

export interface TemplateOptions {
  data: Record<string, any>;
  templateName: string;
}

export class TemplateEngine {
  private templatesDir: string;

  constructor(templatesDir: string) {
    this.templatesDir = templatesDir;
  }

  /**
   * Render a template with the given data
   * @param options Template options containing data and template name
   * @returns Rendered template string
   */
  render(options: TemplateOptions): string {
    const { data, templateName } = options;
    const templatePath = join(this.templatesDir, templateName);
    const template = readFileSync(templatePath, 'utf-8');
    return ejs.render(template, data);
  }

  /**
   * Render a template asynchronously with the given data
   * @param options Template options containing data and template name
   * @returns Promise of rendered template string
   */
  async renderAsync(options: TemplateOptions): Promise<string> {
    const { data, templateName } = options;
    const templatePath = join(this.templatesDir, templateName);
    const template = readFileSync(templatePath, 'utf-8');
    return ejs.render(template, data, { async: true });
  }
} 