import { Theme, createTheme } from '@mui/material/styles';

function getCSSVariable(name: string): string {
  return getComputedStyle(document.body).getPropertyValue(name).trim();
}

export async function pollUntilReady(): Promise<void> {
  while (!document.body.hasAttribute('data-jp-theme-light')) {
    await new Promise(resolve => setTimeout(resolve, 100)); // Wait 100ms
  }
}

export async function getJupyterLabTheme(): Promise<Theme> {
  await pollUntilReady();
  const light = document.body.getAttribute('data-jp-theme-light');
  const primaryFontColor = getCSSVariable('--jp-ui-font-color1');
  return createTheme({
    spacing: 4,
    components: {
      MuiButton: {
        defaultProps: {
          size: 'small'
        }
      },
      MuiFilledInput: {
        defaultProps: {
          margin: 'dense'
        }
      },
      MuiFormControl: {
        defaultProps: {
          margin: 'dense',
          size: 'small'
        }
      },
      MuiFormHelperText: {
        defaultProps: {
          margin: 'dense'
        }
      },
      MuiIconButton: {
        defaultProps: {
          size: 'small'
        }
      },
      MuiInputBase: {
        defaultProps: {
          margin: 'dense',
          size: 'small'
        }
      },
      MuiInputLabel: {
        defaultProps: {
          margin: 'dense'
        }
      },
      MuiListItem: {
        defaultProps: {
          dense: true
        }
      },
      MuiOutlinedInput: {
        defaultProps: {
          margin: 'dense'
        }
      },
      MuiFab: {
        defaultProps: {
          size: 'small'
        }
      },
      MuiTable: {
        defaultProps: {
          size: 'small'
        }
      },
      MuiTextField: {
        defaultProps: {
          margin: 'dense',
          size: 'small'
        }
      },
      MuiToolbar: {
        defaultProps: {
          variant: 'dense'
        }
      }
    },
    palette: {
      background: {
        paper: getCSSVariable('--jp-layout-color1'),
        default: getCSSVariable('--jp-layout-color1')
      },
      mode: light === 'true' ? 'light' : 'dark',
      primary: {
        main: getCSSVariable('--jp-brand-color1'),
        light: getCSSVariable('--jp-brand-color2'),
        dark: getCSSVariable('--jp-brand-color0')
      },
      error: {
        main: getCSSVariable('--jp-error-color1'),
        light: getCSSVariable('--jp-error-color2'),
        dark: getCSSVariable('--jp-error-color0')
      },
      warning: {
        main: getCSSVariable('--jp-warn-color1'),
        light: getCSSVariable('--jp-warn-color2'),
        dark: getCSSVariable('--jp-warn-color0')
      },
      success: {
        main: getCSSVariable('--jp-success-color1'),
        light: getCSSVariable('--jp-success-color2'),
        dark: getCSSVariable('--jp-success-color0')
      },
      text: {
        primary: primaryFontColor,
        secondary: getCSSVariable('--jp-ui-font-color2'),
        disabled: getCSSVariable('--jp-ui-font-color3')
      }
    },
    shape: {
      borderRadius: 2
    },
    typography: {
      fontFamily: getCSSVariable('--jp-ui-font-family'),
      fontSize: 12,
      htmlFontSize: 16,
      button: {
        textTransform: 'capitalize'
      },
      // this is undocumented as of the time of writing.
      // https://stackoverflow.com/a/62950304/12548458
      allVariants: {
        color: primaryFontColor
      }
    }
  });
}
