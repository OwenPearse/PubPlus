import { useRouter } from "expo-router";
import React from "react";
import { ScrollView, StyleSheet, View } from "react-native";

import { SectionHeader } from "@/components/SectionHeader";
import { VenueCard } from "@/components/VenueCard";
import type { Venue } from "@/data/mockData";

type Props = {
  title: string;
  subtitle?: string;
  venues: Venue[];
  savedIds: Set<string>;
  onSave: (id: string) => void;
  onSeeAll?: () => void;
};

export function VenueRow({ title, subtitle, venues, savedIds, onSave, onSeeAll }: Props) {
  const router = useRouter();

  if (venues.length === 0) return null;

  return (
    <View style={styles.section}>
      <SectionHeader
        title={title}
        subtitle={subtitle}
        actionLabel={onSeeAll ? "See all" : undefined}
        onAction={onSeeAll}
      />
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.list}
      >
        {venues.map((venue) => (
          <View key={venue.id} style={styles.card}>
            <VenueCard
              venue={{ ...venue, isSaved: savedIds.has(venue.id) }}
              compact
              onPress={() => router.push(`/venue/${venue.id}`)}
              onSave={() => onSave(venue.id)}
            />
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  section: {
    marginBottom: 8,
  },
  list: {
    paddingHorizontal: 16,
    paddingRight: 32,
    gap: 12,
  },
  card: {
    width: 210,
  },
});
