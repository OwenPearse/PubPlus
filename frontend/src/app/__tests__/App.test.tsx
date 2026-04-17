import { fireEvent, render, screen } from '@testing-library/react-native';

import App from '../App';

describe('App', () => {
  it('renders the Home tab shell', () => {
    render(<App />);
    expect(screen.getByTestId('home-screen')).toBeTruthy();
    expect(screen.getByTestId('home-screen-title')).toBeTruthy();
    expect(screen.getByText('Discovery placeholder')).toBeTruthy();
  });

  it('navigates to Search using the tab bar', () => {
    render(<App />);
    fireEvent.press(screen.getByTestId('tab-search'));
    expect(screen.getByTestId('search-screen')).toBeTruthy();
    expect(screen.getByTestId('search-screen-title')).toBeTruthy();
    expect(screen.getByText('Search placeholder')).toBeTruthy();
  });
});
