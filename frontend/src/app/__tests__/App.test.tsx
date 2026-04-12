import { render, screen } from '@testing-library/react-native';

import App from '../App';

describe('App', () => {
  it('renders the Home tab shell', () => {
    render(<App />);
    expect(screen.getByTestId('home-screen-title')).toBeTruthy();
    expect(screen.getByText('Discovery placeholder')).toBeTruthy();
  });
});
