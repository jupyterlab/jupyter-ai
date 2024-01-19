import { Popup, showPopup } from '@jupyterlab/statusbar';
import React from 'react';
import { VDomModel, VDomRenderer } from '@jupyterlab/ui-components';
import { CommandRegistry } from '@lumino/commands';
import { MenuSvg, RankedMenu, IRankedMenu } from '@jupyterlab/ui-components';
import { Jupyternaut } from '../icons';
import type { IJaiStatusItem } from '../tokens';

/**
 * The Jupyter AI status item, shown in the status bar on the bottom right by
 * default.
 */
export class JaiStatusItem
  extends VDomRenderer<VDomModel>
  implements IJaiStatusItem
{
  constructor(options: JaiStatusItem.IOptions) {
    super(new VDomModel());
    this._commandRegistry = options.commandRegistry;
    this._items = [];

    this.addClass('jp-mod-highlighted');
    this.title.caption = 'Open Jupyternaut status menu';
    this.node.addEventListener('click', this._handleClick);
  }

  /**
   * Adds a menu item to the JAI status item.
   */
  addItem(item: IRankedMenu.IItemOptions): void {
    this._items.push(item);
  }

  /**
   * Returns whether the status item has any menu items.
   */
  hasItems(): boolean {
    return this._items.length !== 0;
  }

  /**
   * Returns the status item as a JSX element.
   */
  render(): JSX.Element | null {
    if (!this.model) {
      return null;
    }
    return <Jupyternaut top={'2px'} width={'16px'} stylesheet={'statusBar'} />;
  }

  dispose(): void {
    this.node.removeEventListener('click', this._handleClick);
    super.dispose();
  }

  /**
   * Create a menu for viewing status and changing options.
   */
  private _handleClick = () => {
    if (this._popup) {
      this._popup.dispose();
    }
    if (this._menu) {
      this._menu.dispose();
    }
    this._menu = new RankedMenu({
      commands: this._commandRegistry,
      renderer: MenuSvg.defaultRenderer
    });
    for (const item of this._items) {
      this._menu.addItem(item);
    }
    this._popup = showPopup({
      body: this._menu,
      anchor: this,
      align: 'left'
    });
  };

  private _items: IRankedMenu.IItemOptions[];
  private _commandRegistry: CommandRegistry;
  private _menu: RankedMenu | null = null;
  private _popup: Popup | null = null;
}

/**
 * A namespace for JupyternautStatus statics.
 */
export namespace JaiStatusItem {
  /**
   * Options for the JupyternautStatus item.
   */
  export interface IOptions {
    /**
     * The application command registry.
     */
    commandRegistry: CommandRegistry;
  }
}
