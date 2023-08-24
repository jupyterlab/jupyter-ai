export type ICellType = null | 'markdown' | 'code';

export interface ICell {
  content: string;
  type: ICellType;
}
