export type ICellType = null | 'markdown' | 'code' | 'output';

// This cell is used as logic for code completion
export interface ICell {
  content: string;
  type: ICellType;
}
